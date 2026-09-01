from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Area, AreaEncounter, DropEntry, Item, Job, Monster


class Command(BaseCommand):
    help = "建立中國鬼怪文學題材的第一版垂直切片資料"

    @transaction.atomic
    def handle(self, *args, **options):
        Job.objects.update_or_create(
            name="遊方客",
            defaults={
                "required_level": 1,
                "enabled": True,
                "source_work": "",
                "source_reference": "中國志怪文學中的遊歷者意象",
                "adaptation_type": Job.AdaptationType.ORIGINAL,
                "lore_note": "玩家進入職業體系前的初始身分。",
            },
        )
        area, _ = Area.objects.update_or_create(
            name="蘭若古道",
            defaults={
                "description": "通往荒寺的幽暗古道，夜行者常在此遇見狐影與遊魂。",
                "required_level": 1,
                "cooldown_seconds": 3,
                "enabled": True,
                "source_work": "《聊齋志異》",
                "source_reference": "〈聶小倩〉的蘭若寺與志怪旅途意象",
                "adaptation_type": Area.AdaptationType.ADAPTED,
                "lore_note": "首個垂直切片場地；借用蘭若意象，地形與遭遇配置為遊戲改編。",
            },
        )
        weapon, _ = Item.objects.update_or_create(
            name="桃木劍",
            defaults={
                "item_type": Item.Type.WEAPON,
                "weapon_type": "劍",
                "atk_bonus": 2,
                "rarity": "common",
                "source_work": "",
                "source_reference": "中國民間桃木辟邪意象",
                "adaptation_type": Item.AdaptationType.ORIGINAL,
                "lore_note": "初始武器；數值與取得方式為遊戲原創。",
            },
        )
        armor, _ = Item.objects.update_or_create(
            name="舊道袍",
            defaults={
                "item_type": Item.Type.ARMOR,
                "defense_bonus": 2,
                "rarity": "common",
                "source_work": "",
                "source_reference": "中國志怪文學中的方士服飾意象",
                "adaptation_type": Item.AdaptationType.ORIGINAL,
                "lore_note": "一般防具，不對應特定原典器物。",
            },
        )
        ring, _ = Item.objects.update_or_create(
            name="狐紋古玉",
            defaults={
                "item_type": Item.Type.ACCESSORY,
                "agility_bonus": 1,
                "rarity": "rare",
                "source_work": "《聊齋志異》",
                "source_reference": "多篇狐鬼故事的狐魅意象",
                "adaptation_type": Item.AdaptationType.ADAPTED,
                "lore_note": "物品名稱與能力為遊戲改編，非原典具名器物。",
            },
        )
        remnant, _ = Item.objects.update_or_create(
            name="陰氣殘縷",
            defaults={
                "item_type": Item.Type.MATERIAL,
                "rarity": "common",
                "source_work": "",
                "source_reference": "中國鬼怪文學的陰氣意象",
                "adaptation_type": Item.AdaptationType.ORIGINAL,
                "lore_note": "供初期掉落與後續製作系統使用的原創材料。",
            },
        )
        monsters = [
            ("遊魂", {"level": 1, "max_hp": 16, "atk": 5, "defense": 1, "agility": 2, "exp_reward": 45, "gold_min": 4, "gold_max": 8, "source_work": "", "source_reference": "中國志怪文學常見的亡魂意象", "adaptation_type": Monster.AdaptationType.ORIGINAL, "lore_note": "首區普通怪物，名稱與能力為遊戲原創。"}, 55),
            ("狐魅", {"level": 2, "max_hp": 22, "atk": 7, "defense": 2, "agility": 7, "exp_reward": 65, "gold_min": 7, "gold_max": 12, "source_work": "《聊齋志異》", "source_reference": "多篇狐鬼故事的狐魅意象", "adaptation_type": Monster.AdaptationType.ADAPTED, "lore_note": "綜合狐魅題材改編，不指涉單一原典角色。"}, 30),
            ("畫皮鬼", {"level": 3, "max_hp": 30, "atk": 8, "defense": 3, "agility": 5, "critical": Decimal("0.020"), "exp_reward": 85, "gold_min": 12, "gold_max": 20, "source_work": "《聊齋志異》", "source_reference": "〈畫皮〉", "adaptation_type": Monster.AdaptationType.ADAPTED, "lore_note": "依畫皮惡鬼意象改編為初期精英怪物。"}, 15),
        ]
        created = {}
        for name, defaults, weight in monsters:
            monster, _ = Monster.objects.update_or_create(name=name, defaults=defaults)
            AreaEncounter.objects.update_or_create(area=area, monster=monster, defaults={"weight": weight})
            created[name] = monster
        DropEntry.objects.update_or_create(monster=created["遊魂"], item=armor, defaults={"drop_rate": Decimal("0.080000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["狐魅"], item=ring, defaults={"drop_rate": Decimal("0.005000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["畫皮鬼"], item=remnant, defaults={"drop_rate": Decimal("0.300000"), "min_quantity": 1, "max_quantity": 2})
        DropEntry.objects.update_or_create(monster=created["畫皮鬼"], item=weapon, defaults={"drop_rate": Decimal("0.050000"), "min_quantity": 1, "max_quantity": 1})
        self.stdout.write(self.style.SUCCESS("中國鬼怪文學題材的第一版遊戲資料已建立。"))
