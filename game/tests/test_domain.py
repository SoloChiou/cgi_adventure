import random

from django.test import SimpleTestCase

from game.domain import (
    ENEMY_SIDE,
    PLAYER_SIDE,
    BattleSide,
    BattleState,
    CombatUnit,
    critical_rate,
    exp_to_next_level,
    hit_rate,
    simulate_battle,
)


def fighter(unit_id, side=PLAYER_SIDE, **overrides):
    values = {
        "unit_id": unit_id,
        "side": side,
        "source": "player" if side == PLAYER_SIDE else "monster",
        "name": unit_id,
        "hp": 30,
        "mp": 10,
        "max_hp": 30,
        "max_mp": 10,
        "atk": 8,
        "defense": 3,
        "intelligence": 3,
        "magic_defense": 2,
        "agility": 5,
        "critical": 0,
    }
    values.update(overrides)
    return CombatUnit(**values)


def battle(player_units, enemy_units, seed, max_rounds=100):
    return simulate_battle(
        BattleSide(PLAYER_SIDE, player_units),
        BattleSide(ENEMY_SIDE, enemy_units),
        random.Random(seed),
        max_rounds=max_rounds,
    )


class FormulaTests(SimpleTestCase):
    def test_hit_rate_is_clamped(self):
        self.assertEqual(hit_rate(1000, 0), 0.98)
        self.assertEqual(hit_rate(0, 1000), 0.20)

    def test_critical_rate_is_clamped(self):
        self.assertEqual(critical_rate(1, 1000, 0), 0.50)
        self.assertEqual(critical_rate(0, 0, 1000), 0.05)

    def test_exp_formula(self):
        self.assertEqual(exp_to_next_level(1), 100)
        self.assertEqual(exp_to_next_level(4), 800)


class BattleTests(SimpleTestCase):
    def test_fixed_seed_reproduces_result(self):
        first = battle([fighter("player:1")], [fighter("monster:1", ENEMY_SIDE)], 1234)
        second = battle([fighter("player:1")], [fighter("monster:1", ENEMY_SIDE)], 1234)
        self.assertEqual(first, second)

    def test_faster_player_kills_before_counterattack(self):
        result = battle(
            [fighter("player:1", atk=100, agility=10)],
            [fighter("monster:1", ENEMY_SIDE, hp=1, max_hp=1, agility=1)],
            1,
        )
        self.assertEqual(result.result, "win")
        self.assertEqual(result.end_reason, "monster_dead")
        self.assertEqual(len(result.rounds[0]["events"]), 1)

    def test_faster_monster_can_attack_first(self):
        result = battle(
            [fighter("player:1", agility=1)],
            [fighter("monster:1", ENEMY_SIDE, agility=10, atk=100)],
            1,
        )
        self.assertEqual(result.result, "lose")
        self.assertEqual(result.rounds[0]["events"][0]["actor_unit_id"], "monster:1")

    def test_round_limit_is_loss(self):
        result = battle(
            [fighter("player:1", atk=1, defense=100)],
            [fighter("monster:1", ENEMY_SIDE, atk=1, defense=100)],
            3,
            max_rounds=1,
        )
        self.assertEqual(result.end_reason, "round_limit")
        for round_data in result.rounds:
            for event in round_data["events"]:
                self.assertGreaterEqual(event["hp_after"], 0)

    def test_one_player_can_target_two_enemies_in_sequence(self):
        result = battle(
            [fighter("player:1", atk=100, agility=10)],
            [
                fighter("monster:1", ENEMY_SIDE, hp=1, max_hp=1, agility=1),
                fighter("monster:2", ENEMY_SIDE, hp=1, max_hp=1, agility=1),
            ],
            1,
        )
        player_events = [
            event
            for round_data in result.rounds
            for event in round_data["events"]
            if event["actor_unit_id"] == "player:1"
        ]
        self.assertEqual(result.result, "win")
        self.assertEqual(result.end_reason, "enemy_side_defeated")
        self.assertEqual([event["target_unit_ids"] for event in player_events], [["monster:1"], ["monster:2"]])

    def test_side_rejects_mismatched_unit(self):
        with self.assertRaisesMessage(ValueError, "BattleSide"):
            BattleSide(PLAYER_SIDE, [fighter("monster:1", ENEMY_SIDE)])

    def test_battle_rejects_duplicate_side_keys(self):
        with self.assertRaisesMessage(ValueError, "不同"):
            BattleState(
                BattleSide(PLAYER_SIDE, [fighter("player:1")]),
                BattleSide(PLAYER_SIDE, [fighter("player:2")]),
            )
