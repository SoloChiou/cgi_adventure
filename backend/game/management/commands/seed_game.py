from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from game.monster_data import load_monster_ini
from game.models import Area, AreaEncounter, EquipmentSet, Item, Job, JobTitle, Monster, Player, Skill
from game.services import recalculate_player_stats


MONSTER_INI_PATH = Path(__file__).resolve().parents[2] / "data" / "monster.ini"


class Command(BaseCommand):
    help = "建立遊戲初始資料與 FF Adventure 參考怪物資料"

    @transaction.atomic
    def handle(self, *args, **options):
        Area.objects.filter(name__in=("蘭若古道", "等級模擬場")).update(enabled=False)
        starter_job, _ = Job.objects.update_or_create(
            name="遊方客",
            defaults={
                "name_en": "Wanderer",
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
            ("武者", "Warrior", "physical", (12, 0, 0, 0, 0, 0, 0), ["刀", "劍", "槍"], "破邪斬", "Evil-Rending Slash"),
            ("方士", "Mystic", "magical", (0, 12, 0, 0, 0, 0, 0), ["法劍", "法杖", "符器"], "五行符", "Five Elements Talisman"),
            ("祝由師", "Ritual Healer", "magical", (0, 0, 12, 0, 0, 0, 8), ["法杖", "符器"], "祝由祓煞", "Ritual Banishment"),
            ("夜行客", "Night Rogue", "physical", (0, 0, 0, 0, 12, 8, 0), ["短刃", "劍"], "夜襲", "Night Assault"),
            ("山林獵手", "Wilds Hunter", "physical", (10, 8, 8, 11, 10, 8, 8), ["弓", "弩", "刀"], "伏妖箭", "Demon-Subduing Arrow"),
            ("丹師", "Alchemist", "magical", (0, 13, 0, 0, 13, 0, 0), ["法杖", "符器"], "丹火化形", "Elixir Flame Transmutation"),
            ("樂師", "Minstrel", "magical", (0, 10, 0, 0, 12, 8, 12), ["樂器", "短刃"], "清商鎮魂", "Pure Melody Soulward"),
            ("通靈者", "Spirit Medium", "magical", (10, 14, 0, 14, 0, 0, 10), ["法杖", "符器"], "通幽神念", "Netherworld Communion"),
            ("神女", "Divine Maiden", "physical", (10, 0, 11, 11, 10, 11, 8), ["槍", "劍"], "神女降魔", "Divine Demonfall"),
            ("法主", "Arcane Hierophant", "magical", (0, 15, 15, 0, 0, 0, 8), ["法杖", "法劍"], "萬法歸一", "Convergence of All Arts"),
            ("仙門宗主", "Immortal Sect Master", "physical", (12, 9, 12, 12, 9, 9, 14), ["劍", "法劍"], "仙門敕令", "Immortal Sect Edict"),
            ("劍客", "Swordmaster", "physical", (12, 11, 0, 9, 12, 14, 8), ["劍"], "御劍疾斬", "Swift Flying Sword"),
            ("行者", "Ascetic", "physical", (13, 8, 13, 0, 10, 13, 8), ["拳套", "棍"], "金剛伏魔", "Vajra Demon Subdual"),
            ("影衛", "Shadow Guard", "physical", (12, 10, 10, 12, 12, 12, 0), ["短刃", "劍"], "無影絕殺", "Shadowless Execution"),
        ]
        jobs = {starter_job.name: starter_job}
        adapted_jobs = {"方士", "祝由師", "丹師"}
        for name, name_en, archetype, requirements, weapon_types, skill_name, skill_name_en in job_rows:
            job, _ = Job.objects.update_or_create(
                name=name,
                defaults={
                    "name_en": name_en,
                    "archetype": archetype,
                    "required_level": 1,
                    "tier": Job.Tier.FIRST,
                    "prerequisite_job": starter_job,
                    "max_hp_bonus": 0, "max_mp_bonus": 0, "atk_bonus": 0, "defense_bonus": 0,
                    "intelligence_bonus": 0, "magic_defense_bonus": 0, "agility_bonus": 0,
                    "critical_bonus": Decimal("0.000"),
                    "required_strength": requirements[0], "required_intellect": requirements[1],
                    "required_piety": requirements[2], "required_vitality": requirements[3],
                    "required_dexterity": requirements[4], "required_speed": requirements[5],
                    "required_charisma": requirements[6], "allowed_weapon_types": weapon_types,
                    "enabled": True,
                    "source_work": "",
                    "source_reference": "中國志怪、武俠、佛教護法、方術與術數意象；詳見 CONTENT_DESIGN.md",
                    "adaptation_type": Job.AdaptationType.ADAPTED if name in adapted_jobs else Job.AdaptationType.ORIGINAL,
                    "lore_note": "七特性門檻參考 FF Adventure；名稱、技能與題材定位詳見 CONTENT_DESIGN.md。",
                },
            )
            jobs[name] = job
        title_rows = {
            "武者": [("習武人", "Martial Initiate"), ("持刃士", "Blade Bearer"), ("破陣武士", "Linebreaker"), ("鎮關豪傑", "Pass Warden"), ("伏妖戰將", "Demonbane General"), ("百戰宗師", "Master of a Hundred Battles"), ("蕩魔武聖", "Demon-Quelling War Saint")],
            "方士": [("習符童", "Talisman Novice"), ("行法士", "Rite Adept"), ("五行術者", "Fivefold Caster"), ("役鬼方士", "Spirit Binder"), ("玄壇法師", "Arcane Altar Master"), ("通天真人", "Heaven-Reaching Sage"), ("乾坤道宗", "Sovereign of Heaven and Earth")],
            "祝由師": [("習祝者", "Ritual Novice"), ("安魂使", "Soul Soother"), ("禳災師", "Calamity Averter"), ("護命祝官", "Life-Warding Ritualist"), ("百病祓師", "Master of Banishment"), ("回春聖手", "Sage of Renewal"), ("濟世祝宗", "Grand Ritual Healer")],
            "夜行客": [("探夜人", "Night Scout"), ("潛蹤客", "Veiled Strider"), ("飛簷手", "Rooftop Runner"), ("無聲刺客", "Silent Assassin"), ("逐影豪俠", "Shadow Chaser"), ("幽都夜使", "Nocturne Envoy"), ("萬影魁首", "Sovereign of Shadows")],
            "山林獵手": [("尋跡人", "Trail Seeker"), ("山徑斥候", "Mountain Scout"), ("伏妖弓手", "Demonstalker Archer"), ("百獸獵師", "Beastwise Hunter"), ("荒野巡狩", "Warden of the Wilds"), ("群山守望", "Sentinel of the Peaks"), ("萬嶺獵宗", "Master of Ten Thousand Ridges")],
            "丹師": [("採藥童", "Herb Gatherer"), ("煉火徒", "Crucible Adept"), ("調鼎師", "Cauldron Crafter"), ("百草丹師", "Elixir Herbalist"), ("玄爐妙手", "Mystic Crucible Master"), ("九轉丹宗", "Master of Ninefold Elixirs"), ("造化藥君", "Lord of Transmutation")],
            "樂師": [("習律人", "Melody Novice"), ("清音客", "Pure-Tone Minstrel"), ("鎮魂樂師", "Soulward Musician"), ("幽弦妙手", "Master of Phantom Strings"), ("百曲宗匠", "Virtuoso of a Hundred Songs"), ("天籟樂聖", "Sage of Celestial Harmony"), ("萬靈知音", "Voice of All Spirits")],
            "通靈者": [("感靈人", "Spirit Sensitive"), ("問魂使", "Soul Inquirer"), ("通幽客", "Netherworld Seer"), ("御念師", "Mindweaver"), ("萬象靈媒", "Medium of Myriad Forms"), ("陰陽先知", "Oracle Between Realms"), ("太虛通靈聖", "Sage of the Great Void")],
            "神女": [("奉燈女", "Lamp Bearer"), ("護祠使", "Shrine Warden"), ("玄甲神女", "Mystic-Armed Maiden"), ("逐邪戰姬", "Bane-Chasing Champion"), ("天門女將", "General of the Heavenly Gate"), ("九霄英靈", "Heroine of the Nine Heavens"), ("鎮世神姬", "World-Warding Divine Maiden")],
            "法主": [("研法者", "Arcane Scholar"), ("講法師", "Doctrine Keeper"), ("掌壇使", "Altar Custodian"), ("統法尊者", "Exalted Arcanist"), ("萬法宗師", "Master of Myriad Arts"), ("天章法主", "Hierophant of the Celestial Canon"), ("玄穹聖宗", "Sovereign of the Mystic Firmament")],
            "仙門宗主": [("外門執事", "Outer Court Steward"), ("內門護法", "Inner Court Guardian"), ("傳功長老", "Teaching Hall Elder"), ("一峰之主", "Master of One Peak"), ("仙門掌教", "Head of the Immortal Sect"), ("群仙盟主", "Lord of the Immortal Alliance"), ("萬宗共主", "Sovereign of Ten Thousand Sects")],
            "劍客": [("試劍人", "Sword Aspirant"), ("行劍客", "Wandering Swordsman"), ("疾風劍士", "Gale Swordsman"), ("御劍名家", "Flying Sword Adept"), ("斬妖劍豪", "Demon-Slaying Swordmaster"), ("凌霄劍宗", "Sky-Piercing Sword Sage"), ("一劍天尊", "Celestial Sword Sovereign")],
            "行者": [("苦行人", "Wayfaring Ascetic"), ("鍛體者", "Body-Tempering Adept"), ("伏魔行者", "Demon-Subduing Pilgrim"), ("金身護法", "Golden-Body Guardian"), ("無畏尊者", "Fearless Venerable"), ("明心大師", "Master of the Clear Mind"), ("渡世聖行", "World-Crossing Sage")],
            "影衛": [("候影人", "Shadow Watcher"), ("潛行衛", "Veiled Guard"), ("無聲刃", "Silent Blade"), ("夜幕使", "Envoy of Night"), ("千面影衛", "Thousand-Faced Guard"), ("無形統領", "Commander Unseen"), ("幽影至尊", "Sovereign of Hidden Shadows")],
        }
        level_ranges = ((1, 6), (7, 13), (14, 20), (21, 27), (28, 34), (35, 41), (42, 99))
        for job_name, titles in title_rows.items():
            for rank, ((min_level, max_level), (title_name, title_name_en)) in enumerate(zip(level_ranges, titles), 1):
                JobTitle.objects.update_or_create(job=jobs[job_name], rank=rank, defaults={
                    "min_level": min_level, "max_level": max_level, "name": title_name, "name_en": title_name_en,
                    "source_work": "", "source_reference": "中國志怪與武俠題材的原創稱號；七階結構參考 FF Adventure",
                    "adaptation_type": JobTitle.AdaptationType.ORIGINAL,
                    "lore_note": "名稱為本專案原創；只作身分顯示，不提供能力加成或功能解鎖。",
                })
        active_job_names = {"遊方客", *jobs.keys()}
        legacy_mapping = {
            "金剛力士": "武者", "護法金剛": "武者", "鎮獄神將": "武者",
            "飛燕劍客": "劍客", "流雲劍俠": "劍客", "凌霄劍仙": "劍客",
            "御靈師": "通靈者", "通幽使": "通靈者", "萬靈宗師": "通靈者",
            "五行術士": "方士", "乾坤天師": "方士",
        }
        for legacy_name, target_name in legacy_mapping.items():
            Player.objects.filter(job__name=legacy_name).update(job=jobs[target_name])
        Job.objects.filter(name__in=legacy_mapping).exclude(name__in=active_job_names).update(enabled=False)
        for player in Player.objects.select_related("job").all():
            recalculate_player_stats(player)
            player.save()
            try:
                equipment = player.equipment
            except EquipmentSet.DoesNotExist:
                continue
            if equipment.weapon and equipment.weapon.weapon_type not in player.job.allowed_weapon_types:
                equipment.weapon = None
                equipment.save(update_fields=["weapon"])

        legacy_skill_names = (
            "破邪重擊", "金剛震", "背水一擊", "燕返", "流星趕月", "絕影一閃",
            "靈狐襲", "紙將衝陣", "火符咒", "五雷咒", "鎮邪咒", "護法棍",
            "伏魔震", "金剛伏魔棍", "流雲十三式", "雲蹤斬", "流雲快劍",
            "幽冥鬼卒", "攝魂靈獸", "幽燈引魂", "五行烈焰", "水雷法", "五行咒",
            "鎮獄破", "神將怒", "神將戰戟", "凌霄一劍", "劍落九霄", "御劍凌空",
            "萬靈朝宗", "神將敕令", "萬靈共鳴", "乾坤雷劫", "天罡鎮煞", "乾坤法印",
        )
        for index, legacy_skill_name in enumerate(legacy_skill_names, 100):
            Skill.objects.filter(name=legacy_skill_name).update(enabled=False, priority=index)
        for job_name, _, archetype, _, _, skill_name, skill_name_en in job_rows:
            Skill.objects.update_or_create(name=skill_name, defaults={
                "name_en": skill_name_en, "job": jobs[job_name], "priority": 1, "mp_cost": 4, "damage_type": archetype,
                "power_multiplier": Decimal("1.50"), "trigger_rate": Decimal("0.350"),
                "accuracy_modifier": Decimal("0.000"), "condition": Skill.Condition.ALWAYS, "enabled": True,
                "source_work": "", "source_reference": "十四職業代表技能；詳見 CONTENT_DESIGN.md",
                "adaptation_type": Skill.AdaptationType.ORIGINAL,
                "lore_note": "名稱為本專案原創；首版共用技能數值，留待戰鬥平衡階段調整。",
            })
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
        try:
            monsters = load_monster_ini(MONSTER_INI_PATH)
        except (OSError, UnicodeError, ValueError) as error:
            raise CommandError(str(error)) from error
        Monster.objects.filter(name__in=("遊魂", "狐魅", "畫皮鬼")).delete()
        for monster_data in monsters:
            Monster.objects.update_or_create(name=monster_data.name, defaults={
                "name_en": monster_data.name_en,
                "reference_hp_range": monster_data.hp_range,
                "level": 1,
                "max_hp": monster_data.max_hp,
                "max_mp": 0,
                "atk": monster_data.atk,
                "defense": 0,
                "intelligence": 0,
                "magic_defense": 0,
                "agility": 0,
                "critical": Decimal("0.000"),
                "exp_reward": monster_data.exp_reward,
                "gold_min": 0,
                "gold_max": 0,
                "source_work": "FF Adventure",
                "source_reference": "reference/ffadventure/ini/monster.ini",
                "adaptation_type": Monster.AdaptationType.ADAPTED,
                "lore_note": "名稱已轉譯為繁體中文與英文；戰鬥數值沿用參考資料。",
            })
        exploration, _ = Area.objects.update_or_create(name="冒險探索", defaults={
            "description": "展開冒險之旅。",
            "required_level": 1,
            "cooldown_seconds": 3,
            "is_level_simulation": False,
            "encounter_weight_mode": Area.EncounterWeightMode.REFERENCE_HP,
            "encounter_monster_hp_min": 0,
            "encounter_monster_hp_max": 499,
            "enabled": True,
            "source_work": "FF Adventure",
            "source_reference": "reference/ffadventure/ffadventure.cgi monster",
            "adaptation_type": Area.AdaptationType.ADAPTED,
            "lore_note": "從完整怪物表依玩家最大 HP 與怪物 HP 隨機值計算遭遇權重。",
        })
        active_monsters = list(Monster.objects.filter(name__in=[row.name for row in monsters]))
        exploration_monsters = [monster for monster in active_monsters if monster.max_hp < 500]
        exploration.encounters.exclude(monster__in=exploration_monsters).delete()
        for monster in exploration_monsters:
            AreaEncounter.objects.update_or_create(area=exploration, monster=monster, defaults={"weight": 1})
        forest, _ = Area.objects.update_or_create(name="魔之森林", defaults={
            "description": "沉睡著強大魔物的駭人森林。",
            "required_level": 1,
            "cooldown_seconds": 3,
            "is_level_simulation": False,
            "encounter_weight_mode": Area.EncounterWeightMode.REFERENCE_HP,
            "encounter_monster_hp_min": 500,
            "encounter_monster_hp_max": None,
            "enabled": True,
            "source_work": "FF Adventure",
            "source_reference": "reference/ffadventure/ffadventure.cgi monster",
            "adaptation_type": Area.AdaptationType.ADAPTED,
            "lore_note": "只收錄 MaxHP 大於或等於 500 的怪物，並沿用冒險探索權重。",
        })
        forest_monsters = [monster for monster in active_monsters if monster.max_hp >= 500]
        forest.encounters.exclude(monster__in=forest_monsters).delete()
        for monster in forest_monsters:
            AreaEncounter.objects.update_or_create(area=forest, monster=monster, defaults={"weight": 1})
        self.stdout.write(self.style.SUCCESS("遊戲初始資料與雙語怪物資料已建立。"))
