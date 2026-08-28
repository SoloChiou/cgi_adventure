import math
from dataclasses import asdict, dataclass
from typing import Dict, List


MAX_ROUNDS = 100
PLAYER_SIDE = "player"
ENEMY_SIDE = "enemy"


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def hit_rate(attacker_agility, defender_agility, modifier=0.0):
    return clamp(0.90 + (attacker_agility - defender_agility) * 0.005 + modifier, 0.20, 0.98)


def critical_rate(attacker_critical, attacker_agility, defender_agility):
    return clamp(0.05 + float(attacker_critical) + max(0, attacker_agility - defender_agility) * 0.001, 0, 0.50)


def exp_to_next_level(level):
    return math.floor(100 * level ** 1.5)


@dataclass
class CombatUnit:
    unit_id: str
    side: str
    source: str
    name: str
    hp: int
    mp: int
    max_hp: int
    max_mp: int
    atk: int
    defense: int
    intelligence: int
    magic_defense: int
    agility: int
    critical: float

    @property
    def alive(self):
        return self.hp > 0


@dataclass
class BattleSide:
    key: str
    units: List[CombatUnit]

    def __post_init__(self):
        if not self.units:
            raise ValueError("戰鬥隊伍至少需要一個單位。")
        if any(unit.side != self.key for unit in self.units):
            raise ValueError("戰鬥單位的 side 必須與 BattleSide 相同。")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("同一隊伍內的 unit_id 不得重複。")

    @property
    def living_units(self):
        return [unit for unit in self.units if unit.alive]

    @property
    def defeated(self):
        return not self.living_units


@dataclass
class BattleState:
    player_side: BattleSide
    enemy_side: BattleSide

    def __post_init__(self):
        if self.player_side.key == self.enemy_side.key:
            raise ValueError("對戰雙方必須使用不同的 BattleSide key。")
        all_ids = [unit.unit_id for unit in self.player_side.units + self.enemy_side.units]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("同一場戰鬥的 unit_id 不得重複。")

    def opposing_side(self, unit):
        if unit.side == self.player_side.key:
            return self.enemy_side
        if unit.side == self.enemy_side.key:
            return self.player_side
        raise ValueError("戰鬥單位不屬於目前 BattleState。")


@dataclass
class BattleOutcome:
    result: str
    end_reason: str
    rounds: List[Dict]
    unit_states: Dict[str, Dict]


def build_turn_order(state):
    side_priority = {state.player_side.key: 0, state.enemy_side.key: 1}
    units = state.player_side.units + state.enemy_side.units
    original_position = {unit.unit_id: index for index, unit in enumerate(units)}
    return sorted(
        units,
        key=lambda unit: (-unit.agility, side_priority[unit.side], original_position[unit.unit_id]),
    )


def select_target(state, attacker):
    targets = state.opposing_side(attacker).living_units
    return targets[0] if targets else None


def _attack(attacker: CombatUnit, target: CombatUnit, rng, round_number: int):
    chance_to_hit = hit_rate(attacker.agility, target.agility)
    hit_roll = rng.random()
    event = {
        "round": round_number,
        "actor": attacker.unit_id,
        "actor_unit_id": attacker.unit_id,
        "actor_name": attacker.name,
        "target": target.unit_id,
        "target_unit_ids": [target.unit_id],
        "target_name": target.name,
        "action_type": "attack",
        "skill_id": None,
        "hit": hit_roll < chance_to_hit,
        "critical": False,
        "damage": 0,
        "hp_before": target.hp,
        "hp_after": target.hp,
        "random_rolls": {"hit": hit_roll},
    }
    if not event["hit"]:
        return event

    variance = rng.uniform(0.90, 1.10)
    crit_chance = critical_rate(attacker.critical, attacker.agility, target.agility)
    crit_roll = rng.random()
    critical = crit_roll < crit_chance
    base_damage = max(1, attacker.atk - target.defense)
    damage = max(1, math.floor(base_damage * variance * (1.5 if critical else 1)))
    target.hp = max(0, target.hp - damage)
    event.update({
        "critical": critical,
        "damage": damage,
        "hp_after": target.hp,
        "random_rolls": {"hit": hit_roll, "variance": variance, "critical": crit_roll},
    })
    return event


def _unit_states(state):
    return {
        unit.unit_id: {"hp": unit.hp, "mp": unit.mp, "alive": unit.alive}
        for unit in state.player_side.units + state.enemy_side.units
    }


def _outcome(state, rounds):
    if state.enemy_side.defeated:
        reason = "monster_dead" if len(state.enemy_side.units) == 1 else "enemy_side_defeated"
        return BattleOutcome("win", reason, rounds, _unit_states(state))
    if state.player_side.defeated:
        reason = "player_dead" if len(state.player_side.units) == 1 else "player_side_defeated"
        return BattleOutcome("lose", reason, rounds, _unit_states(state))
    return None


def simulate_battle(player_side: BattleSide, enemy_side: BattleSide, rng, max_rounds=MAX_ROUNDS):
    state = BattleState(player_side=player_side, enemy_side=enemy_side)
    rounds = []
    turn_order = build_turn_order(state)
    for round_number in range(1, max_rounds + 1):
        events = []
        for attacker in turn_order:
            if not attacker.alive:
                continue
            target = select_target(state, attacker)
            if target is None:
                break
            events.append(_attack(attacker, target, rng, round_number))
            outcome = _outcome(state, rounds + [{"round": round_number, "events": events}])
            if outcome:
                return outcome
        rounds.append({"round": round_number, "events": events})
    return BattleOutcome("lose", "round_limit", rounds, _unit_states(state))


def combat_unit_dict(unit):
    return asdict(unit)
