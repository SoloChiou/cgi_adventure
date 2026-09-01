import random
import secrets
from dataclasses import asdict
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .domain import (
    ENEMY_SIDE,
    PLAYER_SIDE,
    BattleSide,
    CombatSkill,
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
    Job,
    Player,
    PlayerItem,
    WeaponProficiency,
)


class BattleCooldown(ValidationError):
    pass


LEVEL_STAT_GROWTH = {
    "max_hp": 5,
    "max_mp": 2,
    "atk": 2,
    "defense": 1,
    "agility": 1,
}
BASE_ATK = 8
BASE_INTELLIGENCE = 3


def available_job_transitions(player):
    if player.job.tier >= Job.Tier.THIRD:
        return Job.objects.none()
    return Job.objects.filter(
        enabled=True,
        prerequisite_job=player.job,
        tier=player.job.tier + 1,
        required_level__lte=player.level,
    ).order_by("id")


def apply_job_transition(player, target_job):
    if target_job.prerequisite_job_id != player.job_id:
        raise ValidationError("不能跳階或轉入其他職業路線。")
    if target_job.tier != player.job.tier + 1 or player.level < target_job.required_level:
        raise ValidationError("目前尚未符合轉職條件。")
    _replace_job_bonus(player, target_job)
    player.job_count += 1
    player.hp = player.max_hp
    player.mp = player.max_mp
    player.save()
    return player


def _replace_job_bonus(player, target_job):
    old_job = player.job
    if old_job.archetype != target_job.archetype:
        _convert_level_attack_growth(player, old_job, target_job)
    for player_field, job_field in (
        ("max_hp", "max_hp_bonus"),
        ("max_mp", "max_mp_bonus"),
        ("atk", "atk_bonus"),
        ("defense", "defense_bonus"),
        ("intelligence", "intelligence_bonus"),
        ("magic_defense", "magic_defense_bonus"),
        ("agility", "agility_bonus"),
        ("critical", "critical_bonus"),
    ):
        value = getattr(player, player_field) - getattr(old_job, job_field) + getattr(target_job, job_field)
        setattr(player, player_field, value)
    player.job = target_job


def _convert_level_attack_growth(player, old_job, target_job):
    if old_job.archetype == target_job.archetype:
        return
    if old_job.archetype == Job.Archetype.PHYSICAL and target_job.archetype == Job.Archetype.MAGICAL:
        growth = max(0, player.atk - BASE_ATK - old_job.atk_bonus)
        player.atk -= growth
        player.intelligence += growth
    elif old_job.archetype == Job.Archetype.MAGICAL and target_job.archetype == Job.Archetype.PHYSICAL:
        growth = max(0, player.intelligence - BASE_INTELLIGENCE - old_job.intelligence_bonus)
        player.intelligence -= growth
        player.atk += growth


def set_development_player_state(player, *, target_level, target_job, target_hp):
    level_delta = target_level - player.level
    growth_fields = dict(LEVEL_STAT_GROWTH)
    if target_job.archetype == Job.Archetype.MAGICAL:
        growth_fields.pop("atk")
        growth_fields["intelligence"] = 2
    for field, growth in growth_fields.items():
        setattr(player, field, max(1, getattr(player, field) + level_delta * growth))
    player.level = target_level
    if target_job.pk != player.job_id:
        _replace_job_bonus(player, target_job)
    if target_hp > player.max_hp:
        raise ValidationError("目前 HP 不得超過調整後的 MaxHP。")
    player.hp = target_hp
    player.mp = min(player.mp, player.max_mp)
    player.job_count = target_job.tier
    player.save()
    return player


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
    job_skills = player.job.skills.filter(enabled=True).order_by("priority", "id")
    skills = [
        CombatSkill(
            skill_id=skill.id,
            name=skill.name,
            mp_cost=skill.mp_cost,
            damage_type=skill.damage_type,
            power_multiplier=float(skill.power_multiplier),
            trigger_rate=float(skill.trigger_rate),
            accuracy_modifier=float(skill.accuracy_modifier),
            condition=skill.condition,
        )
        for skill in job_skills
    ]
    return CombatUnit(
        unit_id="player:{}".format(player.pk), side=PLAYER_SIDE, source="player",
        name=player.name, hp=player.hp, mp=player.mp,
        max_hp=player.max_hp, max_mp=player.max_mp,
        atk=player.atk + bonuses["atk"], defense=player.defense + bonuses["defense"],
        intelligence=player.intelligence, magic_defense=player.magic_defense,
        agility=player.agility + bonuses["agility"], critical=float(player.critical),
        level=player.level, skills=skills, attack_type=player.job.archetype,
    )


def monster_combat_unit(monster, instance_number=1):
    return scaled_monster_combat_unit(monster, monster.level, instance_number)


def scaled_monster_combat_unit(monster, target_level, instance_number=1):
    level_delta = max(0, target_level - monster.level)
    max_hp = monster.max_hp + level_delta * 8
    max_mp = monster.max_mp + level_delta * 3
    return CombatUnit(
        unit_id="monster:{}:{}".format(monster.pk, instance_number), side=ENEMY_SIDE, source="monster",
        name=monster.name, hp=max_hp, mp=max_mp,
        max_hp=max_hp, max_mp=max_mp,
        atk=monster.atk + level_delta * 2,
        defense=monster.defense + level_delta,
        intelligence=monster.intelligence + level_delta * 2,
        magic_defense=monster.magic_defense + level_delta,
        agility=monster.agility + level_delta,
        critical=float(monster.critical),
        level=target_level,
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
        growth_fields = LEVEL_STAT_GROWTH
        if player.job.archetype == Job.Archetype.MAGICAL:
            growth_fields = {**LEVEL_STAT_GROWTH, "atk": 0, "intelligence": 2}
        for field, growth in growth_fields.items():
            if not growth:
                continue
            setattr(player, field, getattr(player, field) + growth)
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
    if area.is_level_simulation and not settings.DEBUG:
        raise PermissionDenied("此區域只在本機開發環境開放。")
    if player.level < area.required_level:
        raise PermissionDenied("角色等級不足，無法進入此地區。")
    if player.last_battle_at and now < player.last_battle_at + timedelta(seconds=area.cooldown_seconds):
        remaining = (player.last_battle_at + timedelta(seconds=area.cooldown_seconds) - now).total_seconds()
        raise BattleCooldown("請等待 {:.1f} 秒後再戰鬥。".format(max(0, remaining)))

    random_seed = seed if seed is not None else secrets.randbits(63)
    rng = random.Random(random_seed)
    monster = choose_monster(area, rng)
    player_before = player_combat_unit(player)
    monster_level = player.level if area.is_level_simulation else monster.level
    monster_snapshot = scaled_monster_combat_unit(monster, monster_level)
    player_unit = player_combat_unit(player)
    monster_unit = scaled_monster_combat_unit(monster, monster_level)
    outcome = simulate_battle(
        BattleSide(PLAYER_SIDE, [player_unit]),
        BattleSide(ENEMY_SIDE, [monster_unit]),
        rng,
    )
    player_state = outcome.unit_states[player_unit.unit_id]
    player.last_battle_at = now
    if outcome.result == "win" and not area.is_level_simulation:
        player.hp = player_state["hp"]
        player.mp = player_state["mp"]
        rewards = _apply_rewards(player, monster, rng)
    elif outcome.result == "win":
        player.hp = player_state["hp"]
        player.mp = player_state["mp"]
        rewards = {"exp": 0, "gold": 0, "drops": [], "proficiency": None, "level_ups": []}
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
