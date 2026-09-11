import random
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone

from game.models import Area, AreaEncounter, BattleRecord, EquipmentSet, GameAccount, Item, Job, Monster, Player, PlayerItem, Skill
from game.services import BattleCooldown, apply_job_transition, available_job_transitions, choose_monster, player_combat_unit, run_battle, scaled_monster_combat_unit, set_development_player_state, validate_initial_traits


class BattleServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="hero", password="password")
        account = GameAccount.objects.create(user=self.user)
        job = Job.objects.create(name="初心者")
        self.player = Player.objects.create(account=account, name="測試勇者", job=job, atk=100, agility=100)
        self.area = Area.objects.create(name="測試區", cooldown_seconds=3)
        self.monster = Monster.objects.create(
            name="木樁", name_en="Wooden Dummy", level=1, max_hp=1, atk=1, defense=0, agility=0,
            critical=Decimal("0"), exp_reward=250, gold_min=5, gold_max=5,
        )
        AreaEncounter.objects.create(area=self.area, monster=self.monster, weight=1)

    def test_reference_encounter_weights_match_ff_adventure_formula(self):
        self.area.encounter_weight_mode = Area.EncounterWeightMode.REFERENCE_HP
        self.area.save(update_fields=["encounter_weight_mode"])
        self.monster.reference_hp_range = 2
        self.monster.save(update_fields=["reference_hp_range"])
        tougher = Monster.objects.create(
            name="強敵", max_hp=10, atk=2, defense=0, exp_reward=2,
            gold_min=0, gold_max=0, reference_hp_range=4,
        )
        AreaEncounter.objects.create(area=self.area, monster=tougher)

        class RecordingRandom:
            def choices(self, population, weights, k):
                self.population = population
                self.weights = weights
                self.k = k
                return [population[0]]

        rng = RecordingRandom()
        selected = choose_monster(self.area, rng, player_max_hp=100)

        self.assertEqual(selected, self.monster)
        self.assertEqual(rng.weights, [50, 25])
        self.assertEqual(rng.k, 1)

    def test_area_hp_bounds_filter_encounters(self):
        self.area.encounter_monster_hp_max = 499
        self.area.save(update_fields=["encounter_monster_hp_max"])
        strong = Monster.objects.create(name="高 HP 怪物", max_hp=500, atk=2, defense=0, exp_reward=2, gold_min=0, gold_max=0)
        AreaEncounter.objects.create(area=self.area, monster=strong)

        class RecordingRandom:
            def choices(self, population, weights, k):
                self.population = population
                return [population[0]]

        selected = choose_monster(self.area, RecordingRandom(), player_max_hp=100)
        self.assertEqual(selected, self.monster)

    def test_win_rewards_and_can_level_multiple_times(self):
        result = run_battle(user=self.user, area_id=self.area.pk, seed=1)
        self.player.refresh_from_db()
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["rewards"]["gold"], 5)
        self.assertEqual(result["rewards"]["victory_count"], 1)
        self.assertEqual(result["rewards"]["battle_count"], 1)
        self.assertNotIn("drops", result["rewards"])
        self.assertNotIn("proficiency", result["rewards"])
        self.assertEqual(self.player.level, 2)
        self.assertEqual(BattleRecord.objects.count(), 1)
        self.assertEqual(result["monster_snapshot"]["name_en"], "Wooden Dummy")
        event = result["rounds"][0]["events"][0]
        self.assertEqual(event["actor_unit_id"], "player:{}".format(self.player.pk))
        self.assertEqual(event["target_unit_ids"], ["monster:{}:1".format(self.monster.pk)])
        self.assertEqual(event["target_name_en"], "Wooden Dummy")
        self.assertTrue(result["narratives"]["zh-TW"])
        self.assertTrue(result["narratives"]["en"])

    def test_cooldown_blocks_second_reward(self):
        now = timezone.now()
        run_battle(user=self.user, area_id=self.area.pk, seed=1, now=now)
        with self.assertRaises(BattleCooldown):
            run_battle(user=self.user, area_id=self.area.pk, seed=2, now=now + timedelta(seconds=1))
        self.assertEqual(BattleRecord.objects.count(), 1)

    def test_settlement_failure_rolls_back_everything(self):
        before_exp = self.player.exp
        with patch("game.services._apply_rewards", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                run_battle(user=self.user, area_id=self.area.pk, seed=1)
        self.player.refresh_from_db()
        self.assertEqual(self.player.exp, before_exp)
        self.assertIsNone(self.player.last_battle_at)
        self.assertEqual(BattleRecord.objects.count(), 0)

    def test_loss_has_no_rewards_and_restores_quarter_hp(self):
        self.player.atk = 1
        self.player.defense = 0
        self.player.agility = 0
        self.player.save()
        self.monster.max_hp = 500
        self.monster.atk = 100
        self.monster.agility = 100
        self.monster.save()
        result = run_battle(user=self.user, area_id=self.area.pk, seed=4)
        self.player.refresh_from_db()
        self.assertEqual(result["result"], "lose")
        self.assertEqual(result["rewards"]["exp"], 0)
        self.assertEqual(self.player.hp, max(1, self.player.max_hp // 4))

    def test_unowned_equipment_is_rejected(self):
        sword = Item.objects.create(name="不存在背包的劍", item_type=Item.Type.WEAPON)
        EquipmentSet.objects.create(player=self.player, weapon=sword)
        with self.assertRaisesMessage(ValidationError, "角色未持有"):
            run_battle(user=self.user, area_id=self.area.pk, seed=1)

    def test_job_weapon_restriction_is_enforced(self):
        self.player.job.allowed_weapon_types = ["劍"]
        self.player.job.save(update_fields=["allowed_weapon_types"])
        bow = Item.objects.create(name="測試弓", item_type=Item.Type.WEAPON, weapon_type="弓")
        PlayerItem.objects.create(player=self.player, item=bow)
        EquipmentSet.objects.create(player=self.player, weapon=bow)
        with self.assertRaisesMessage(ValidationError, "不能使用"):
            run_battle(user=self.user, area_id=self.area.pk, seed=1)

    @override_settings(DEBUG=True)
    def test_level_simulation_matches_player_level_and_has_no_rewards(self):
        simulation_area = Area.objects.create(name="等級模擬場", cooldown_seconds=0, is_level_simulation=True)
        simulation_monster = Monster.objects.create(
            name="修行幻影", level=1, max_hp=24, max_mp=10, atk=6, defense=2,
            intelligence=6, magic_defense=2, agility=4, critical=Decimal("0.020"),
            exp_reward=0, gold_min=0, gold_max=0,
        )
        AreaEncounter.objects.create(area=simulation_area, monster=simulation_monster)
        self.player.level = 25
        self.player.atk = 300
        self.player.agility = 300
        self.player.save(update_fields=["level", "atk", "agility"])
        before_exp = self.player.exp

        result = run_battle(user=self.user, area_id=simulation_area.pk, seed=11)

        self.assertEqual(result["monster_snapshot"]["level"], 25)
        self.assertEqual(result["monster_snapshot"]["max_hp"], 216)
        self.assertEqual(result["rewards"]["exp"], 0)
        self.assertEqual(result["rewards"]["gold"], 0)
        self.player.refresh_from_db()
        self.assertEqual(self.player.exp, before_exp)

    def test_level_simulation_scaling_at_validation_levels(self):
        template = Monster.objects.create(
            name="縮放幻影", level=1, max_hp=24, max_mp=10, atk=6, defense=2,
            intelligence=6, magic_defense=2, agility=4, critical=Decimal("0.020"),
            exp_reward=0, gold_min=0, gold_max=0,
        )
        for level in (1, 25, 50, 99):
            unit = scaled_monster_combat_unit(template, level)
            delta = level - 1
            self.assertEqual(unit.level, level)
            self.assertEqual(unit.max_hp, 24 + delta * 8)
            self.assertEqual(unit.atk, 6 + delta * 2)
            self.assertEqual(unit.defense, 2 + delta)
            self.assertEqual(unit.agility, 4 + delta)

    @override_settings(DEBUG=False)
    def test_level_simulation_is_rejected_outside_debug(self):
        simulation_area = Area.objects.create(name="等級模擬場", is_level_simulation=True)
        with self.assertRaisesMessage(PermissionDenied, "本機開發"):
            run_battle(user=self.user, area_id=simulation_area.pk, seed=1)


class JobProgressionServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="progression", password="password")
        account = GameAccount.objects.create(user=user)
        self.starter = Job.objects.create(name="遊方客", tier=Job.Tier.STARTER)
        self.first = Job.objects.create(
            name="武者", tier=Job.Tier.FIRST, required_level=5, prerequisite_job=self.starter, required_strength=12,
            max_hp_bonus=30, max_mp_bonus=5, atk_bonus=6, defense_bonus=8,
            magic_defense_bonus=5, agility_bonus=-2,
        )
        self.second = Job.objects.create(
            name="方士", tier=Job.Tier.FIRST, required_level=25, prerequisite_job=self.starter, required_intellect=12,
            max_hp_bonus=55, max_mp_bonus=10, atk_bonus=11, defense_bonus=15,
            magic_defense_bonus=9, agility_bonus=-2,
        )
        self.player = Player.objects.create(account=account, name="修行者", job=self.starter, level=44, exp=9000, gold=777)

    def test_transition_resets_level_exp_traits_and_combat_state(self):
        self.player.strength = 12
        self.player.save(update_fields=["strength"])
        apply_job_transition(self.player, self.first)
        self.player.refresh_from_db()
        self.assertEqual(self.player.level, 1)
        self.assertEqual(self.player.exp, 0)
        self.assertEqual(self.player.gold, 777)
        self.assertEqual(
            [self.player.strength, self.player.intellect, self.player.piety, self.player.vitality, self.player.dexterity, self.player.speed, self.player.charisma],
            [12, 8, 8, 9, 9, 8, 8],
        )
        self.assertEqual(self.player.hp, self.player.max_hp)
        self.assertEqual(self.player.mp, self.player.max_mp)
        self.assertEqual(self.player.job_count, 1)

        self.player.intellect = 12
        self.player.save(update_fields=["intellect"])
        apply_job_transition(self.player, self.second)
        self.player.refresh_from_db()
        self.assertEqual(self.player.level, 1)
        self.assertEqual(self.player.strength, 9)
        self.assertEqual(self.player.intellect, 12)
        self.assertEqual(self.player.job_count, 2)

    def test_transition_recalculates_both_attack_stats_from_traits(self):
        magical = Job.objects.create(
            name="法主", tier=Job.Tier.FIRST, required_level=5, prerequisite_job=self.starter,
            intelligence_bonus=10, archetype=Job.Archetype.MAGICAL,
        )
        self.player.level = 5
        self.player.atk = 16  # base 8 + four levels of ATK growth
        self.player.save(update_fields=["level", "atk"])
        apply_job_transition(self.player, magical)
        self.player.refresh_from_db()
        self.assertEqual(self.player.atk, 8)
        self.assertEqual(self.player.intelligence, 13)

    def test_level_up_recalculates_stats_from_level_and_traits(self):
        magical = Job.objects.create(name="法術職", tier=Job.Tier.FIRST, archetype=Job.Archetype.MAGICAL, intelligence_bonus=10)
        self.player.job = magical
        self.player.level = 1
        self.player.atk = 8
        self.player.intelligence = 3
        self.player.exp = 100
        self.player.save(update_fields=["job", "level", "atk", "intelligence", "exp"])
        from game.services import _apply_level_ups
        _apply_level_ups(self.player, random.Random(0))
        self.assertEqual(self.player.intelligence, 15)
        self.assertEqual(self.player.atk, 10)

    def test_level_up_trait_growth_is_reproducible(self):
        self.player.level = 1
        self.player.exp = 100
        self.player.save(update_fields=["level", "exp"])
        from game.services import _apply_level_ups
        _apply_level_ups(self.player, random.Random(1))
        self.assertEqual(self.player.strength, 10)
        self.assertEqual(
            [self.player.intellect, self.player.piety, self.player.vitality, self.player.dexterity, self.player.speed, self.player.charisma],
            [8, 8, 9, 9, 8, 8],
        )

    def test_transition_rejects_repeating_current_job(self):
        self.player.strength = 12
        self.player.save(update_fields=["strength"])
        apply_job_transition(self.player, self.first)
        with self.assertRaisesMessage(ValidationError, "目前職業"):
            apply_job_transition(self.player, self.first)
        self.player.refresh_from_db()
        self.assertEqual(self.player.job_count, 1)

    def test_available_transitions_ignore_level_and_exclude_current_job(self):
        self.player.strength = 12
        self.assertEqual(list(available_job_transitions(self.player)), [self.first])
        self.player.level = 1
        self.player.job = self.first
        self.player.intellect = 12
        self.assertEqual(list(available_job_transitions(self.player)), [self.second])

    def test_available_transitions_respect_trait_requirements(self):
        self.player.strength = 11
        self.player.save(update_fields=["strength"])
        self.assertFalse(available_job_transitions(self.player).exists())
        self.player.strength = 12
        self.player.save(update_fields=["strength"])
        self.assertEqual(list(available_job_transitions(self.player)), [self.first])

    def test_transition_unequips_incompatible_weapon_without_deleting_it(self):
        self.player.strength = 12
        self.player.save(update_fields=["strength"])
        weapon = Item.objects.create(name="舊弓", item_type=Item.Type.WEAPON, weapon_type="弓")
        PlayerItem.objects.create(player=self.player, item=weapon)
        equipment = EquipmentSet.objects.create(player=self.player, weapon=weapon)
        self.first.allowed_weapon_types = ["劍"]
        self.first.save(update_fields=["allowed_weapon_types"])

        apply_job_transition(self.player, self.first)

        equipment.refresh_from_db()
        self.assertIsNone(equipment.weapon)
        self.assertTrue(PlayerItem.objects.filter(player=self.player, item=weapon, quantity=1).exists())

    @patch("game.services.recalculate_player_stats", side_effect=RuntimeError("recalculation failed"))
    def test_transition_rolls_back_every_change_when_recalculation_fails(self, _recalculate):
        self.player.strength = 12
        self.player.save(update_fields=["strength"])
        with self.assertRaisesMessage(RuntimeError, "recalculation failed"):
            apply_job_transition(self.player, self.first)

        self.player.refresh_from_db()
        self.assertEqual(self.player.job, self.starter)
        self.assertEqual(self.player.level, 44)
        self.assertEqual(self.player.exp, 9000)
        self.assertEqual(self.player.job_count, 0)

    def test_initial_traits_require_exactly_ten_points(self):
        traits = {"strength": 12, "intellect": 8, "piety": 8, "vitality": 16, "dexterity": 9, "speed": 8, "charisma": 8}
        self.assertEqual(validate_initial_traits(traits), traits)
        traits["vitality"] = 15
        with self.assertRaisesMessage(ValidationError, "正好分配 10 點"):
            validate_initial_traits(traits)

    def test_development_level_adjustment_applies_each_level_growth(self):
        set_development_player_state(
            self.player,
            target_level=10,
            target_job=self.starter,
            target_hp=20,
        )
        self.player.refresh_from_db()
        self.assertEqual(self.player.level, 10)
        self.assertEqual(self.player.max_hp, 75)
        self.assertEqual(self.player.max_mp, 28)
        self.assertEqual(self.player.atk, 26)
        self.assertEqual(self.player.defense, 12)
        self.assertEqual(self.player.agility, 14)
        self.assertEqual(self.player.hp, 20)

    def test_development_job_change_replaces_bonus_and_sets_hp(self):
        set_development_player_state(
            self.player,
            target_level=5,
            target_job=self.first,
            target_hp=40,
        )
        self.player.refresh_from_db()
        self.assertEqual(self.player.job, self.first)
        self.assertEqual(self.player.max_hp, 80)
        self.assertEqual(self.player.atk, 22)
        self.assertEqual(self.player.hp, 40)
        self.assertEqual(self.player.job_count, 1)

    def test_development_hp_cannot_exceed_adjusted_maximum(self):
        with self.assertRaisesMessage(ValidationError, "不得超過"):
            set_development_player_state(
                self.player,
                target_level=5,
                target_job=self.starter,
                target_hp=999,
            )

    def test_development_level_must_be_between_one_and_ninety_nine(self):
        for target_level in (0, 100):
            with self.subTest(target_level=target_level), self.assertRaisesMessage(ValidationError, "1 至 99"):
                set_development_player_state(
                    self.player,
                    target_level=target_level,
                    target_job=self.starter,
                    target_hp=self.player.hp,
                )


class JobSkillAssignmentServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="skills", password="password")
        account = GameAccount.objects.create(user=user)
        self.job = Job.objects.create(name="方士", tier=Job.Tier.FIRST)
        self.other_job = Job.objects.create(name="劍客", tier=Job.Tier.FIRST)
        self.player = Player.objects.create(account=account, name="術者", job=self.job)
        self.skills = [
            Skill.objects.create(job=self.job, name="術法{}".format(index), priority=index, mp_cost=1, damage_type="magical", power_multiplier=1.5, trigger_rate=1)
            for index in range(1, 4)
        ]

    def test_combat_unit_automatically_uses_all_current_job_skills_in_priority_order(self):
        unit = player_combat_unit(self.player)
        self.assertEqual([skill.name for skill in unit.skills], ["術法1", "術法2", "術法3"])

    def test_job_transition_replaces_available_skill_set(self):
        next_job = Job.objects.create(name="武者", tier=Job.Tier.FIRST)
        next_skill = Skill.objects.create(job=next_job, name="五行咒", priority=1, mp_cost=2, damage_type="magical", power_multiplier=1.6, trigger_rate=1)
        self.player = apply_job_transition(self.player, next_job)
        self.assertEqual([skill.skill_id for skill in player_combat_unit(self.player).skills], [next_skill.id])


class ConcurrentJobTransitionTests(TransactionTestCase):
    reset_sequences = True

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_duplicate_transition_only_succeeds_once(self):
        test_database_name = connection.settings_dict["NAME"]

        def create_fixture():
            close_old_connections()
            connections["default"].settings_dict["NAME"] = test_database_name
            user = get_user_model().objects.create_user(username="concurrent-transition")
            account = GameAccount.objects.create(user=user)
            current = Job.objects.create(name="武者", tier=Job.Tier.FIRST)
            target = Job.objects.create(name="方士", tier=Job.Tier.FIRST)
            player = Player.objects.create(account=account, name="並行修行者", job=current)
            close_old_connections()
            return player.pk, target.pk

        with ThreadPoolExecutor(max_workers=1) as executor:
            player_id, target_id = executor.submit(create_fixture).result()
        barrier = threading.Barrier(2)

        def transition():
            close_old_connections()
            connections["default"].settings_dict["NAME"] = test_database_name
            player = Player.objects.get(pk=player_id)
            target = Job.objects.get(pk=target_id)
            barrier.wait()
            try:
                apply_job_transition(player, target)
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: transition(), range(2)))

        player = Player.objects.get(pk=player_id)
        self.assertEqual(results.count(True), 1)
        self.assertEqual(player.job_id, target_id)
        self.assertEqual(player.job_count, 1)
