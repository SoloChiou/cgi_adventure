from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from game.models import Area, AreaEncounter, DropEntry, GameAccount, Item, Job, JobTitle, Monster, Player, Skill


class SeedGameTests(TestCase):
    def test_seed_game_does_not_create_cancelled_areas(self):
        call_command("seed_game", verbosity=0)

        self.assertFalse(Area.objects.filter(name__in=("蘭若古道", "等級模擬場")).exists())
        self.assertTrue(Area.objects.filter(name="冒險探索", enabled=True).exists())

    def test_seed_game_creates_translated_reference_monsters_idempotently(self):
        cancelled_area = Area.objects.create(name="蘭若古道", enabled=True)
        cancelled_simulation = Area.objects.create(name="等級模擬場", enabled=True, is_level_simulation=True)
        call_command("seed_game", verbosity=0)
        call_command("seed_game", verbosity=0)

        self.assertEqual(Job.objects.filter(name="遊方客").count(), 1)
        self.assertEqual(Job.objects.count(), 15)
        self.assertEqual(Job.objects.filter(enabled=True, tier=Job.Tier.FIRST).count(), 14)
        self.assertEqual(Job.objects.get(name="武者").required_strength, 12)
        self.assertEqual(Job.objects.get(name="通靈者").required_intellect, 14)
        self.assertEqual(Job.objects.get(name="影衛").required_speed, 12)
        self.assertEqual(Job.objects.get(name="劍客").allowed_weapon_types, ["劍"])
        self.assertEqual(JobTitle.objects.count(), 98)
        warrior_titles = list(JobTitle.objects.filter(job__name="武者").values_list("rank", "min_level", "max_level", "name", "name_en"))
        self.assertEqual(warrior_titles[0], (1, 1, 6, "習武人", "Martial Initiate"))
        self.assertEqual(warrior_titles[-1], (7, 42, 99, "蕩魔武聖", "Demon-Quelling War Saint"))
        self.assertEqual(Skill.objects.filter(enabled=True).count(), 14)
        self.assertEqual(Job.objects.get(name="法主").skills.get(enabled=True).name, "萬法歸一")
        self.assertEqual(Skill.objects.get(name="萬法歸一").name_en, "Convergence of All Arts")
        cancelled_area.refresh_from_db()
        cancelled_simulation.refresh_from_db()
        self.assertFalse(cancelled_area.enabled)
        self.assertFalse(cancelled_simulation.enabled)
        exploration = Area.objects.get(name="冒險探索")
        self.assertEqual(exploration.encounter_weight_mode, Area.EncounterWeightMode.REFERENCE_HP)
        forest = Area.objects.get(name="魔之森林")
        self.assertEqual(forest.encounter_weight_mode, Area.EncounterWeightMode.REFERENCE_HP)

        self.assertEqual(Monster.objects.count(), 70)
        self.assertEqual(AreaEncounter.objects.filter(area=exploration).count(), 68)
        self.assertEqual(AreaEncounter.objects.filter(area=forest).count(), 2)
        self.assertTrue(all(row.monster.max_hp < 500 for row in exploration.encounters.select_related("monster")))
        self.assertTrue(all(row.monster.max_hp >= 500 for row in forest.encounters.select_related("monster")))
        self.assertEqual(Item.objects.count(), 4)
        self.assertEqual(DropEntry.objects.count(), 0)

        rat = Monster.objects.get(name="鼠")
        self.assertEqual(rat.name_en, "Rat")
        self.assertEqual(rat.exp_reward, 15)
        self.assertEqual(rat.reference_hp_range, 3)
        self.assertEqual(rat.max_hp, 5)
        self.assertEqual(rat.atk, 2)
        dragon = Monster.objects.get(name="巨龍")
        self.assertEqual(dragon.name_en, "Dragon")
        self.assertEqual(dragon.exp_reward, 3000)
        self.assertEqual(dragon.max_hp, 999)
        self.assertEqual(dragon.atk, 200)
        self.assertEqual(dragon.source_reference, "reference/ffadventure/ini/monster.ini")

    def test_seed_game_rolls_back_when_monster_ini_is_invalid(self):
        existing = Monster.objects.create(
            name="保留怪物", max_hp=1, atk=1, defense=0, exp_reward=1, gold_min=0, gold_max=0
        )
        with TemporaryDirectory() as directory:
            invalid_path = Path(directory) / "monster.ini"
            invalid_path.write_text("未知怪物<>1<>1<>1<>1<>\n", encoding="utf-8")
            with patch("game.management.commands.seed_game.MONSTER_INI_PATH", invalid_path):
                with self.assertRaises(CommandError):
                    call_command("seed_game", verbosity=0)

        self.assertTrue(Monster.objects.filter(pk=existing.pk, name="保留怪物").exists())

    def test_seed_game_maps_legacy_spirit_job_to_spirit_medium(self):
        legacy = Job.objects.create(name="御靈師", tier=Job.Tier.FIRST)
        user = get_user_model().objects.create_user(username="legacy-player")
        player = Player.objects.create(account=GameAccount.objects.create(user=user), name="舊角色", job=legacy)

        call_command("seed_game", verbosity=0)

        player.refresh_from_db()
        legacy.refresh_from_db()
        self.assertEqual(player.job.name, "通靈者")
        self.assertFalse(legacy.enabled)



class EnsureDevelopmentAdminTests(TestCase):
    @override_settings(DEBUG=True, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_creates_superuser_with_configured_password(self):
        call_command("ensure_dev_admin", verbosity=0)
        user = get_user_model().objects.get(username="test-admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("Test-only@not-a-credential"))
