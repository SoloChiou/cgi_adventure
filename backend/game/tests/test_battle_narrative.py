from django.test import SimpleTestCase

from game.battle_narrative import BattleNarrativeComposer


def event(**overrides):
    values = {
        "actor_unit_id": "player:1", "actor_name": "遊方客", "actor_name_en": "Wanderer",
        "target_unit_ids": ["monster:1"], "target_name": "巨鼠", "target_name_en": "Giant Rat",
        "action_type": "attack", "skill_name": None, "skill_name_en": None,
        "hit": True, "critical": False, "damage": 12,
    }
    values.update(overrides)
    return values


class BattleNarrativeComposerTests(SimpleTestCase):
    def test_same_seed_reproduces_same_lines(self):
        rounds = [{"round": 1, "events": [event()]}]
        self.assertEqual(
            BattleNarrativeComposer(42).compose(rounds, "zh-TW"),
            BattleNarrativeComposer(42).compose(rounds, "zh-TW"),
        )

    def test_produces_traditional_chinese_and_english(self):
        rounds = [{"round": 1, "events": [event(action_type="skill", skill_name="破邪斬", skill_name_en="Evil-Banishing Slash")]}]
        zh_line = BattleNarrativeComposer(7).compose(rounds, "zh-TW")[0]
        en_line = BattleNarrativeComposer(7).compose(rounds, "en")[0]
        self.assertIn("破邪斬", zh_line["text"])
        self.assertIn("Evil-Banishing Slash", en_line["text"])
        self.assertEqual(zh_line["tone"], "skill")

    def test_merges_miss_and_immediate_counterattack(self):
        missed = event(
            actor_unit_id="monster:1", actor_name="巨鼠", actor_name_en="Giant Rat",
            target_unit_ids=["player:1"], target_name="遊方客", target_name_en="Wanderer",
            hit=False, damage=0,
        )
        counter = event(action_type="skill", skill_name="破邪斬", skill_name_en="Evil-Banishing Slash", damage=18)
        lines = BattleNarrativeComposer(9).compose([{"round": 1, "events": [missed, counter]}], "zh-TW")
        self.assertEqual(len(lines), 1)
        self.assertTrue("躲過" in lines[0]["text"] or "避開" in lines[0]["text"])
        self.assertIn("破邪斬", lines[0]["text"])
        self.assertIn("18", lines[0]["text"])

    def test_critical_uses_reference_style_tone(self):
        line = BattleNarrativeComposer(3).compose(
            [{"round": 1, "events": [event(critical=True)]}], "zh-TW"
        )[0]
        self.assertEqual(line["event_type"], "critical_hit")
        self.assertEqual(line["tone"], "critical")
        self.assertIn("暴擊", line["text"])

    def test_rejects_unknown_locale(self):
        with self.assertRaisesMessage(ValueError, "語系"):
            BattleNarrativeComposer(1).compose([], "ja")
