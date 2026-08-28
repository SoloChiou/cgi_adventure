from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from game.models import Area, AreaEncounter, BattleRecord, EquipmentSet, GameAccount, Item, Job, Monster, Player, PlayerItem
from game.services import BattleCooldown, run_battle


class BattleServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="hero", password="password")
        account = GameAccount.objects.create(user=self.user)
        job = Job.objects.create(name="初心者")
        self.player = Player.objects.create(account=account, name="測試勇者", job=job, atk=100, agility=100)
        self.area = Area.objects.create(name="測試區", cooldown_seconds=3)
        self.monster = Monster.objects.create(
            name="木樁", level=1, max_hp=1, atk=1, defense=0, agility=0,
            critical=Decimal("0"), exp_reward=250, gold_min=5, gold_max=5,
        )
        AreaEncounter.objects.create(area=self.area, monster=self.monster, weight=1)

    def test_win_rewards_and_can_level_multiple_times(self):
        result = run_battle(user=self.user, area_id=self.area.pk, seed=1)
        self.player.refresh_from_db()
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["rewards"]["gold"], 5)
        self.assertEqual(self.player.level, 2)
        self.assertEqual(BattleRecord.objects.count(), 1)
        event = result["rounds"][0]["events"][0]
        self.assertEqual(event["actor_unit_id"], "player:{}".format(self.player.pk))
        self.assertEqual(event["target_unit_ids"], ["monster:{}:1".format(self.monster.pk)])

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
