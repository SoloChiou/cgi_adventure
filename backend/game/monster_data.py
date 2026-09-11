from dataclasses import dataclass
from pathlib import Path
from typing import List


MONSTER_NAMES = {
    "ラット": ("鼠", "Rat"),
    "キラー・ラット": ("殺手鼠", "Killer Rat"),
    "ラビット・ラット": ("兔鼠", "Rabbit Rat"),
    "ジャイアント・ラット": ("巨鼠", "Giant Rat"),
    "ジェイル・ラット": ("牢獄鼠", "Jail Rat"),
    "ファット・ラット": ("肥碩鼠", "Fat Rat"),
    "クリーピング・バイン": ("匍匐藤", "Creeping Vine"),
    "フューミング・バイン": ("煙霧藤", "Fuming Vine"),
    "ストラングラー・バイン": ("絞殺藤", "Strangler Vine"),
    "ジャングル・バイン": ("叢林藤", "Jungle Vine"),
    "バット": ("蝙蝠", "Bat"),
    "ヒュージ・バット": ("巨型蝙蝠", "Huge Bat"),
    "バンパイア・バット": ("吸血蝙蝠", "Vampire Bat"),
    "インディゴ・バット": ("靛藍蝙蝠", "Indigo Bat"),
    "ローグ": ("盜賊", "Rogue"),
    "スカリーワグ": ("無賴", "Scallywag"),
    "ブッシュワーカー": ("叢林伏擊者", "Bushwhacker"),
    "ブリガンド": ("強盜", "Brigand"),
    "ローグ・リーダー": ("盜賊首領", "Rogue Leader"),
    "パイレーツ": ("海盜", "Pirate"),
    "スライム": ("史萊姆", "Slime"),
    "アシッド・スライム": ("酸液史萊姆", "Acid Slime"),
    "コールド・スライム": ("寒冰史萊姆", "Cold Slime"),
    "ダンジョン・リーチ": ("地牢水蛭", "Dungeon Leech"),
    "ジャイアント・ワーム": ("巨型蠕蟲", "Giant Worm"),
    "ホワイト・ワーム": ("白色蠕蟲", "White Worm"),
    "ジェリー・クラウド": ("膠質雲", "Jelly Cloud"),
    "ゼラチン・ベイパー": ("凝膠蒸氣", "Gelatin Vapor"),
    "フローター": ("漂浮怪", "Floater"),
    "ジェリー・フィッシュ": ("水母", "Jellyfish"),
    "マン・オー・ウォー": ("僧帽水母", "Man-of-War"),
    "ジャイアント・アント": ("巨型螞蟻", "Giant Ant"),
    "フォーリジャー": ("覓食者", "Forager"),
    "バスペス": ("蜂后", "Waspess"),
    "トリックスター": ("詭術師", "Trickster"),
    "マイナー・ドワーフ": ("礦工矮人", "Miner Dwarf"),
    "ロッティング・コープス": ("腐爛屍骸", "Rotting Corpse"),
    "ゾンビ・ボーンズ": ("殭屍骸骨", "Zombie Bones"),
    "ポイズン・バイパー": ("毒蝰蛇", "Poison Viper"),
    "ジャイアント・モスキート": ("巨型蚊", "Giant Mosquito"),
    "ドラゴンフライ": ("蜻蜓", "Dragonfly"),
    "ジャイアント・クラブ": ("巨型螃蟹", "Giant Crab"),
    "ナイトゴーント": ("夜魘", "Nightgaunt"),
    "スピリッツ": ("幽靈群", "Spirits"),
    "バンシー": ("報喪女妖", "Banshee"),
    "フェアリー・シルフ": ("妖精風靈", "Fairy Sylph"),
    "ツイステッド・シルフ": ("扭曲風靈", "Twisted Sylph"),
    "グープ・グループ": ("黏液怪群", "Goop Group"),
    "ヒドラ・プラント": ("多頭蛇植株", "Hydra Plant"),
    "ヒュージ・スパイダー": ("巨型蜘蛛", "Huge Spider"),
    "ハイランダー": ("高地戰士", "Highlander"),
    "ニンジャ": ("忍者", "Ninja"),
    "ヒル・ジャイアント": ("丘陵巨人", "Hill Giant"),
    "アマズール": ("亞馬遜戰士", "Amazul"),
    "アマズール・アーチャー": ("亞馬遜弓手", "Amazul Archer"),
    "シャーマネス": ("女薩滿", "Shamaness"),
    "プリーテス": ("女祭司", "Priestess"),
    "アマズール・ゾンビ": ("亞馬遜殭屍", "Amazul Zombie"),
    "ファイアー・ファラオ": ("烈焰法老", "Fire Pharaoh"),
    "サイレン": ("海妖", "Siren"),
    "サイレン・ソーサリス": ("海妖女術士", "Siren Sorceress"),
    "ゴブリン": ("哥布林", "Goblin"),
    "ゴブリン・シャーマン": ("哥布林薩滿", "Goblin Shaman"),
    "ゴブリン・プリースト": ("哥布林祭司", "Goblin Priest"),
    "スケルトン": ("骷髏", "Skeleton"),
    "デス・ナイト": ("死亡騎士", "Death Knight"),
    "スケルトン・ロード": ("骷髏領主", "Skeleton Lord"),
    "シー・サーペント": ("海蛇", "Sea Serpent"),
    "ドラゴン": ("巨龍", "Dragon"),
    "レッサー・デーモン": ("次級惡魔", "Lesser Demon"),
}


@dataclass(frozen=True)
class MonsterData:
    name: str
    name_en: str
    exp_reward: int
    hp_range: int
    max_hp: int
    atk: int


def load_monster_ini(path: Path) -> List[MonsterData]:
    monsters = []
    seen_names = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        fields = raw_line.split("<>")
        if len(fields) != 6 or fields[-1] != "":
            raise ValueError(f"monster.ini 第 {line_number} 行格式錯誤")
        japanese_name, exp, hp_range, hp_base, damage = fields[:5]
        if japanese_name not in MONSTER_NAMES:
            raise ValueError(f"monster.ini 第 {line_number} 行缺少名稱翻譯：{japanese_name}")
        name, name_en = MONSTER_NAMES[japanese_name]
        if name in seen_names:
            raise ValueError(f"monster.ini 第 {line_number} 行的中文名稱重複：{name}")
        try:
            exp_reward, hp_range, hp_base, damage = map(int, (exp, hp_range, hp_base, damage))
        except ValueError as error:
            raise ValueError(f"monster.ini 第 {line_number} 行包含非整數數值") from error
        if min(exp_reward, hp_range, hp_base, damage) < 0 or hp_range == 0:
            raise ValueError(f"monster.ini 第 {line_number} 行包含無效數值")
        monsters.append(MonsterData(name, name_en, exp_reward, hp_range, hp_range + hp_base - 1, damage))
        seen_names.add(name)
    if not monsters:
        raise ValueError("monster.ini 沒有怪物資料")
    return monsters
