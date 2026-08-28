import random
import secrets
from dataclasses import asdict
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .domain import (
    ENEMY_SIDE,
    PLAYER_SIDE,
    BattleSide,
    CombatUnit,
    combat_unit_dict,
    exp_to_next_level,
    simulate_battle,
)
from .models import (
    Area,
    BattleRecord,
    DropEntry,
    EquipmentSet,
    Player,
    PlayerItem,
    WeaponProficiency,
)


class BattleCooldown(ValidationError):
    pass


def _equipment_bonuses(player):
    bonuses = {"atk": 0, "defense": 0, "agility": 0}
    try:
        equipment = player.equipment
    except EquipmentSet.DoesNotExist:
        return bonuses
    for item in (equipment.weapon, equipment.armor, equipment.accessory):
        if item:
            bonuses["atk"] += item.atk_bonus
            bonuses["defense"] += item.defense_bonus
            bonuses["agility"] += item.agility_bonus
    return bonuses


def _validate_equipment(player):
    try:
        equipment = player.equipment
    except EquipmentSet.DoesNotExist:
        return
    expected_types = {
        "weapon": "weapon",
        "armor": "armor",
        "accessory": "accessory",
    }
    for field, expected_type in expected_types.items():
        item = getattr(equipment, field)
        if not item:
            continue
        if item.item_type != expected_type:
            raise ValidationError("目前裝備欄位包含不合法物品。")
        if not PlayerItem.objects.filter(player=player, item=item, quantity__gt=0).exists():
            raise ValidationError("目前裝備包含角色未持有的物品。")


def player_combat_unit(player):
    bonuses = _equipment_bonuses(player)
    return CombatUnit(
        unit_id="player:{}".format(player.pk), side=PLAYER_SIDE, source="player",
        name=player.name, hp=player.hp, mp=player.mp,
        max_hp=player.max_hp, max_mp=player.max_mp,
        atk=player.atk + bonuses["atk"], defense=player.defense + bonuses["defense"],
        intelligence=player.intelligence, magic_defense=player.magic_defense,
        agility=player.agility + bonuses["agility"], critical=float(player.critical),
    )


def monster_combat_unit(monster, instance_number=1):
    return CombatUnit(
        unit_id="monster:{}:{}".format(monster.pk, instance_number), side=ENEMY_SIDE, source="monster",
        name=monster.name, hp=monster.max_hp, mp=monster.max_mp,
        max_hp=monster.max_hp, max_mp=monster.max_mp, atk=monster.atk,
        defense=monster.defense, intelligence=monster.intelligence,
        magic_defense=monster.magic_defense, agility=monster.agility,
        critical=float(monster.critical),
    )


def choose_monster(area, rng):
    encounters = list(area.encounters.select_related("monster"))
    if not encounters:
        raise ValidationError("此地區目前沒有怪物。")
    return rng.choices([entry.monster for entry in encounters], weights=[entry.weight for entry in encounters], k=1)[0]


def _apply_level_ups(player):
    levels = []
    while player.level < 99 and player.exp >= exp_to_next_level(player.level):
        player.level += 1
        player.max_hp += 5
        player.max_mp += 2
        player.atk += 2
        player.defense += 1
        player.agility += 1
        levels.append(player.level)
    if levels:
        player.hp = player.max_hp
        player.mp = player.max_mp
    return levels


def _apply_drops(player, monster, rng):
    awarded = []
    for entry in monster.drops.select_related("item"):
        if rng.random() < float(entry.drop_rate):
            quantity = rng.randint(entry.min_quantity, entry.max_quantity)
            inventory, _ = PlayerItem.objects.select_for_update().get_or_create(player=player, item=entry.item, defaults={"quantity": 0})
            PlayerItem.objects.filter(pk=inventory.pk).update(quantity=F("quantity") + quantity)
            awarded.append({"item_id": entry.item_id, "name": entry.item.name, "quantity": quantity})
    return awarded


def _apply_rewards(player, monster, rng):
    gold = rng.randint(monster.gold_min, monster.gold_max)
    player.exp += monster.exp_reward
    player.gold += gold
    drops = _apply_drops(player, monster, rng)
    proficiency = None
    try:
        weapon = player.equipment.weapon
    except EquipmentSet.DoesNotExist:
        weapon = None
    if weapon and weapon.weapon_type:
        row, _ = WeaponProficiency.objects.select_for_update().get_or_create(player=player, weapon_type=weapon.weapon_type)
        row.exp = F("exp") + 1
        row.save(update_fields=["exp"])
        proficiency = {"weapon_type": weapon.weapon_type, "exp": 1}
    level_ups = _apply_level_ups(player)
    return {"exp": monster.exp_reward, "gold": gold, "drops": drops, "proficiency": proficiency, "level_ups": level_ups}


@transaction.atomic
def run_battle(*, user, area_id, seed=None, now=None):
    now = now or timezone.now()
    try:
        player = Player.objects.select_for_update().select_related("account", "job").get(account__user=user)
    except Player.DoesNotExist:
        raise PermissionDenied("找不到你的角色。")
    if player.account.status != "active":
        raise PermissionDenied("帳號目前無法進行遊戲。")
    if player.hp <= 0:
        raise ValidationError("角色目前無法戰鬥。")
    _validate_equipment(player)
    area = Area.objects.prefetch_related("encounters__monster").get(pk=area_id, enabled=True)
    if player.level < area.required_level:
        raise PermissionDenied("角色等級不足，無法進入此地區。")
    if player.last_battle_at and now < player.last_battle_at + timedelta(seconds=area.cooldown_seconds):
        remaining = (player.last_battle_at + timedelta(seconds=area.cooldown_seconds) - now).total_seconds()
        raise BattleCooldown("請等待 {:.1f} 秒後再戰鬥。".format(max(0, remaining)))

    random_seed = seed if seed is not None else secrets.randbits(63)
    rng = random.Random(random_seed)
    monster = choose_monster(area, rng)
    player_before = player_combat_unit(player)
    monster_snapshot = monster_combat_unit(monster)
    player_unit = player_combat_unit(player)
    monster_unit = monster_combat_unit(monster)
    outcome = simulate_battle(
        BattleSide(PLAYER_SIDE, [player_unit]),
        BattleSide(ENEMY_SIDE, [monster_unit]),
        rng,
    )
    player_state = outcome.unit_states[player_unit.unit_id]
    player.last_battle_at = now
    if outcome.result == "win":
        player.hp = player_state["hp"]
        player.mp = player_state["mp"]
        rewards = _apply_rewards(player, monster, rng)
    else:
        player.hp = max(1, player.max_hp // 4)
        player.mp = player_state["mp"]
        rewards = {"exp": 0, "gold": 0, "drops": [], "proficiency": None, "level_ups": []}
    player.save()
    record = BattleRecord.objects.create(
        player=player,
        monster_snapshot=combat_unit_dict(monster_snapshot),
        result=outcome.result,
        end_reason=outcome.end_reason,
        rounds=outcome.rounds,
        rewards=rewards,
        random_seed=random_seed,
    )
    return {
        "battle_id": record.pk,
        "random_seed": random_seed,
        "result": outcome.result,
        "end_reason": outcome.end_reason,
        "player_before": combat_unit_dict(player_before),
        "player_after": player_combat_unit(player),
        "monster_snapshot": combat_unit_dict(monster_snapshot),
        "rounds": outcome.rounds,
        "rewards": rewards,
    }
