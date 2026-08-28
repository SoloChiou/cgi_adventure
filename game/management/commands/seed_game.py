from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Area, AreaEncounter, DropEntry, Item, Job, Monster


class Command(BaseCommand):
    help = "建立第一版垂直切片的遊戲資料"

    @transaction.atomic
    def handle(self, *args, **options):
        Job.objects.update_or_create(name="初心者", defaults={"required_level": 1, "enabled": True})
        area, _ = Area.objects.update_or_create(
            name="新手草原",
            defaults={"description": "城鎮外的草原，適合初心者累積實戰經驗。", "required_level": 1, "cooldown_seconds": 3, "enabled": True},
        )
        weapon, _ = Item.objects.update_or_create(
            name="練習木劍",
            defaults={"item_type": Item.Type.WEAPON, "weapon_type": "劍", "atk_bonus": 2, "rarity": "common"},
        )
        armor, _ = Item.objects.update_or_create(
            name="布衣",
            defaults={"item_type": Item.Type.ARMOR, "defense_bonus": 2, "rarity": "common"},
        )
        ring, _ = Item.objects.update_or_create(
            name="草原戒指",
            defaults={"item_type": Item.Type.ACCESSORY, "agility_bonus": 1, "rarity": "rare"},
        )
        fang, _ = Item.objects.update_or_create(name="哥布林牙齒", defaults={"item_type": Item.Type.MATERIAL, "rarity": "common"})
        monsters = [
            ("史萊姆", {"level": 1, "max_hp": 16, "atk": 5, "defense": 1, "agility": 2, "exp_reward": 45, "gold_min": 4, "gold_max": 8}, 55),
            ("野狼", {"level": 2, "max_hp": 22, "atk": 7, "defense": 2, "agility": 7, "exp_reward": 65, "gold_min": 7, "gold_max": 12}, 30),
            ("哥布林", {"level": 3, "max_hp": 30, "atk": 8, "defense": 3, "agility": 5, "critical": Decimal("0.020"), "exp_reward": 85, "gold_min": 12, "gold_max": 20}, 15),
        ]
        created = {}
        for name, defaults, weight in monsters:
            monster, _ = Monster.objects.update_or_create(name=name, defaults=defaults)
            AreaEncounter.objects.update_or_create(area=area, monster=monster, defaults={"weight": weight})
            created[name] = monster
        DropEntry.objects.update_or_create(monster=created["史萊姆"], item=armor, defaults={"drop_rate": Decimal("0.080000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["野狼"], item=ring, defaults={"drop_rate": Decimal("0.005000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["哥布林"], item=fang, defaults={"drop_rate": Decimal("0.300000"), "min_quantity": 1, "max_quantity": 2})
        DropEntry.objects.update_or_create(monster=created["哥布林"], item=weapon, defaults={"drop_rate": Decimal("0.050000"), "min_quantity": 1, "max_quantity": 1})
        self.stdout.write(self.style.SUCCESS("第一版遊戲資料已建立。"))
