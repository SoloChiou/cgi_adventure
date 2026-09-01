from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Area, AreaEncounter, DropEntry, Item, Job, Monster, Skill


class Command(BaseCommand):
    help = "建立中國鬼怪文學題材的第一版垂直切片資料"

    @transaction.atomic
    def handle(self, *args, **options):
        starter_job, _ = Job.objects.update_or_create(
            name="遊方客",
            defaults={
                "required_level": 1,
                "tier": Job.Tier.STARTER,
                "prerequisite_job": None,
                "enabled": True,
                "source_work": "",
                "source_reference": "中國志怪文學中的遊歷者意象",
                "adaptation_type": Job.AdaptationType.ORIGINAL,
                "lore_note": "玩家進入職業體系前的初始身分。",
            },
        )
        job_rows = [
            ("金剛力士", 1, 5, "遊方客", (30, 5, 6, 8, 0, 5, -2, "0.000")),
            ("飛燕劍客", 1, 5, "遊方客", (10, 10, 7, 2, 0, 2, 8, "0.050")),
            ("御靈師", 1, 5, "遊方客", (15, 25, 1, 2, 7, 5, 3, "0.020")),
            ("方士", 1, 5, "遊方客", (5, 35, 0, 1, 10, 6, 1, "0.000")),
            ("護法金剛", 2, 25, "金剛力士", (55, 10, 11, 15, 0, 9, -2, "0.000")),
            ("流雲劍俠", 2, 25, "飛燕劍客", (20, 18, 13, 4, 0, 4, 15, "0.080")),
            ("通幽使", 2, 25, "御靈師", (28, 45, 2, 4, 13, 9, 5, "0.030")),
            ("五行術士", 2, 25, "方士", (12, 60, 0, 2, 18, 11, 2, "0.000")),
            ("鎮獄神將", 3, 50, "護法金剛", (85, 15, 18, 24, 0, 15, -1, "0.020")),
            ("凌霄劍仙", 3, 50, "流雲劍俠", (35, 28, 21, 7, 0, 7, 23, "0.120")),
            ("萬靈宗師", 3, 50, "通幽使", (45, 70, 3, 7, 21, 15, 8, "0.050")),
            ("乾坤天師", 3, 50, "五行術士", (22, 90, 0, 4, 29, 18, 3, "0.020")),
        ]
        jobs = {starter_job.name: starter_job}
        adapted_jobs = {"金剛力士", "護法金剛", "方士", "五行術士", "乾坤天師"}
        for name, tier, required_level, prerequisite_name, bonuses in job_rows:
            max_hp, max_mp, atk, defense, intelligence, magic_defense, agility, critical = bonuses
            job, _ = Job.objects.update_or_create(
                name=name,
                defaults={
                    "required_level": required_level,
                    "tier": tier,
                    "prerequisite_job": jobs[prerequisite_name],
                    "max_hp_bonus": max_hp,
                    "max_mp_bonus": max_mp,
                    "atk_bonus": atk,
                    "defense_bonus": defense,
                    "intelligence_bonus": intelligence,
                    "magic_defense_bonus": magic_defense,
                    "agility_bonus": agility,
                    "critical_bonus": Decimal(critical),
                    "enabled": True,
                    "source_work": "",
                    "source_reference": "中國志怪、武俠、佛教護法、方術與術數意象；詳見 CONTENT_DESIGN.md",
                    "adaptation_type": Job.AdaptationType.ADAPTED if name in adapted_jobs else Job.AdaptationType.ORIGINAL,
                    "lore_note": "能力值與轉職路線為遊戲化設計；題材定位詳見 CONTENT_DESIGN.md。",
                },
            )
            jobs[name] = job
        skill_rows = [
            ("金剛力士", "破邪重擊", 3, "physical", "1.45", "0.350", "0.000", "always"),
            ("金剛力士", "金剛震", 6, "physical", "1.75", "0.250", "-0.050", "target_hp_gte_50"),
            ("金剛力士", "背水一擊", 5, "physical", "2.00", "1.000", "-0.100", "self_hp_lte_30"),
            ("飛燕劍客", "燕返", 3, "physical", "1.35", "0.400", "0.050", "always"),
            ("飛燕劍客", "流星趕月", 6, "physical", "1.80", "0.250", "-0.050", "target_hp_gte_50"),
            ("飛燕劍客", "絕影一閃", 5, "physical", "1.65", "1.000", "0.100", "self_hp_lte_30"),
            ("御靈師", "靈狐襲", 4, "magical", "1.40", "0.350", "0.050", "always"),
            ("御靈師", "紙將衝陣", 7, "magical", "1.75", "0.250", "-0.050", "target_hp_gte_50"),
            ("方士", "火符咒", 4, "magical", "1.50", "0.350", "0.000", "always"),
            ("方士", "五雷咒", 8, "magical", "2.00", "0.250", "-0.100", "target_hp_gte_50"),
            ("方士", "鎮邪咒", 6, "magical", "1.65", "1.000", "0.100", "self_hp_lte_30"),
            ("護法金剛", "護法棍", 8, "physical", "1.90", "0.300", "0.050", "target_hp_gte_50"),
            ("護法金剛", "伏魔震", 7, "physical", "2.30", "1.000", "0.000", "self_hp_lte_30"),
            ("護法金剛", "金剛伏魔棍", 6, "physical", "1.55", "0.350", "0.050", "always"),
            ("流雲劍俠", "流雲十三式", 8, "physical", "1.85", "0.300", "0.050", "target_hp_gte_50"),
            ("流雲劍俠", "雲蹤斬", 7, "physical", "2.00", "1.000", "0.100", "self_hp_lte_30"),
            ("流雲劍俠", "流雲快劍", 6, "physical", "1.60", "0.400", "0.080", "always"),
            ("通幽使", "幽冥鬼卒", 9, "magical", "1.90", "0.300", "0.000", "target_hp_gte_50"),
            ("通幽使", "攝魂靈獸", 8, "magical", "1.70", "1.000", "0.050", "self_hp_lte_30"),
            ("通幽使", "幽燈引魂", 7, "magical", "1.60", "0.350", "0.050", "always"),
            ("五行術士", "五行烈焰", 9, "magical", "2.10", "0.300", "-0.050", "target_hp_gte_50"),
            ("五行術士", "水雷法", 8, "magical", "1.85", "1.000", "0.050", "self_hp_lte_30"),
            ("五行術士", "五行咒", 7, "magical", "1.75", "0.350", "0.000", "always"),
            ("鎮獄神將", "鎮獄破", 11, "physical", "2.40", "0.250", "-0.050", "target_hp_gte_50"),
            ("鎮獄神將", "神將怒", 9, "physical", "3.00", "1.000", "-0.050", "self_hp_lte_30"),
            ("鎮獄神將", "神將戰戟", 8, "physical", "1.90", "0.350", "0.000", "always"),
            ("凌霄劍仙", "凌霄一劍", 12, "physical", "2.45", "0.250", "-0.050", "target_hp_gte_50"),
            ("凌霄劍仙", "劍落九霄", 10, "physical", "3.00", "1.000", "0.050", "self_hp_lte_30"),
            ("凌霄劍仙", "御劍凌空", 8, "physical", "1.95", "0.400", "0.080", "always"),
            ("萬靈宗師", "萬靈朝宗", 13, "magical", "2.50", "0.250", "-0.100", "target_hp_gte_50"),
            ("萬靈宗師", "神將敕令", 11, "magical", "3.15", "1.000", "0.000", "self_hp_lte_30"),
            ("萬靈宗師", "萬靈共鳴", 9, "magical", "2.00", "0.350", "0.050", "always"),
            ("乾坤天師", "乾坤雷劫", 14, "magical", "2.70", "0.200", "-0.150", "target_hp_gte_50"),
            ("乾坤天師", "天罡鎮煞", 11, "magical", "3.25", "1.000", "0.050", "self_hp_lte_30"),
            ("乾坤天師", "乾坤法印", 9, "magical", "2.10", "0.350", "0.000", "always"),
        ]
        job_skill_priorities = {}
        for job_name, name, mp_cost, damage_type, multiplier, trigger, accuracy, condition in skill_rows:
            priority = job_skill_priorities.get(job_name, 0) + 1
            job_skill_priorities[job_name] = priority
            Skill.objects.update_or_create(name=name, defaults={
                "job": jobs[job_name], "priority": priority, "mp_cost": mp_cost, "damage_type": damage_type,
                "power_multiplier": Decimal(multiplier), "trigger_rate": Decimal(trigger),
                "accuracy_modifier": Decimal(accuracy), "condition": condition, "enabled": True,
                "source_work": "", "source_reference": "三階職業戰鬥設計；詳見 PROJECT_SPEC.md",
                "adaptation_type": Skill.AdaptationType.ORIGINAL,
                "lore_note": "名稱與戰鬥數值為遊戲化設計。",
            })
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
        simulation_area, _ = Area.objects.update_or_create(
            name="等級模擬場",
            defaults={
                "description": "依挑戰者目前等級生成同級修行幻影，供本機戰鬥驗證使用。",
                "required_level": 1,
                "cooldown_seconds": 0,
                "is_level_simulation": True,
                "enabled": True,
                "source_work": "",
                "source_reference": "本機戰鬥平衡驗證需求",
                "adaptation_type": Area.AdaptationType.ORIGINAL,
                "lore_note": "DEBUG 專用無獎勵區域；怪物等級與能力由伺服器依角色等級建立當場快照。",
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
        simulation_monster, _ = Monster.objects.update_or_create(
            name="修行幻影",
            defaults={
                "level": 1,
                "max_hp": 24,
                "max_mp": 10,
                "atk": 6,
                "defense": 2,
                "intelligence": 6,
                "magic_defense": 2,
                "agility": 4,
                "critical": Decimal("0.020"),
                "exp_reward": 0,
                "gold_min": 0,
                "gold_max": 0,
                "source_work": "",
                "source_reference": "本機同級戰鬥驗證模板",
                "adaptation_type": Monster.AdaptationType.ORIGINAL,
                "lore_note": "資料庫保存 Lv.1 模板；進入等級模擬場時依角色等級建立戰鬥快照。",
            },
        )
        AreaEncounter.objects.update_or_create(
            area=simulation_area,
            monster=simulation_monster,
            defaults={"weight": 1},
        )
        DropEntry.objects.update_or_create(monster=created["遊魂"], item=armor, defaults={"drop_rate": Decimal("0.080000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["狐魅"], item=ring, defaults={"drop_rate": Decimal("0.005000"), "min_quantity": 1, "max_quantity": 1})
        DropEntry.objects.update_or_create(monster=created["畫皮鬼"], item=remnant, defaults={"drop_rate": Decimal("0.300000"), "min_quantity": 1, "max_quantity": 2})
        DropEntry.objects.update_or_create(monster=created["畫皮鬼"], item=weapon, defaults={"drop_rate": Decimal("0.050000"), "min_quantity": 1, "max_quantity": 1})
        self.stdout.write(self.style.SUCCESS("中國鬼怪文學題材的第一版遊戲資料已建立。"))
