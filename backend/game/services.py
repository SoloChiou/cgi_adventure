import random
import secrets
from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal

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


TRAIT_FIELDS = ("strength", "intellect", "piety", "vitality", "dexterity", "speed", "charisma")
TRAIT_GROWTH_RATE = 0.20
INITIAL_TRAITS = {"strength": 9, "intellect": 8, "piety": 8, "vitality": 9, "dexterity": 9, "speed": 8, "charisma": 8}
INITIAL_BONUS_POINTS = 10


def available_job_transitions(player):
    if player.job.tier >= Job.Tier.THIRD:
        return Job.objects.none()
    return Job.objects.filter(
        enabled=True,
        prerequisite_job=player.job,
        tier=player.job.tier + 1,
        required_level__lte=player.level,
        required_strength__lte=player.strength,
        required_intellect__lte=player.intellect,
        required_piety__lte=player.piety,
        required_vitality__lte=player.vitality,
        required_dexterity__lte=player.dexterity,
        required_speed__lte=player.speed,
        required_charisma__lte=player.charisma,
    ).order_by("id")


def validate_initial_traits(traits):
    normalized = {}
    for field in TRAIT_FIELDS:
        try:
            value = int(traits[field])
        except (KeyError, TypeError, ValueError):
            raise ValidationError("必須提供完整的七種角色特性。")
        base = INITIAL_TRAITS[field]
        if value < base or value > 18:
            raise ValidationError("初始角色特性不得低於基礎值或高於 18。")
        normalized[field] = value
    spent = sum(normalized[field] - INITIAL_TRAITS[field] for field in TRAIT_FIELDS)
    if spent != INITIAL_BONUS_POINTS:
        raise ValidationError("初始角色必須正好分配 10 點特性點數。")
    if max(normalized.values()) < 12:
        raise ValidationError("至少一項初始角色特性必須達到 12。")
    return normalized


def job_requirements_met(job, traits):
    return all(traits[field] >= getattr(job, "required_{}".format(field)) for field in TRAIT_FIELDS)


def apply_job_transition(player, target_job):
    if target_job.prerequisite_job_id != player.job_id:
        raise ValidationError("不能跳階或轉入其他職業路線。")
    if target_job.tier != player.job.tier + 1 or player.level < target_job.required_level:
        raise ValidationError("目前尚未符合轉職條件。")
    if not job_requirements_met(target_job, {field: getattr(player, field) for field in TRAIT_FIELDS}):
        raise ValidationError("角色特性尚未符合此職業門檻。")
    player.job = target_job
    recalculate_player_stats(player)
    player.job_count += 1
    player.hp = player.max_hp
    player.mp = player.max_mp
    player.save()
    return player


def recalculate_player_stats(player):
    """Rebuild persisted combat stats from authoritative level, traits, and job."""
    job = player.job
    player.max_hp = max(1, 5 * player.level + player.vitality + 16 + job.max_hp_bonus)
    player.max_mp = max(1, 2 * player.level + (player.intellect + player.piety) // 2 + job.max_mp_bonus)
    player.atk = max(0, 2 * player.level + player.strength - 3 + job.atk_bonus)
    player.defense = max(0, player.level + player.vitality // 4 + job.defense_bonus)
    player.intelligence = max(0, 2 * player.level + player.intellect - 7 + job.intelligence_bonus)
    player.magic_defense = max(0, (player.piety + player.charisma) // 8 + job.magic_defense_bonus)
    player.agility = max(0, player.level + (player.speed + player.dexterity) // 4 + job.agility_bonus)
    trait_critical = Decimal(max(0, player.dexterity + player.charisma - 17)) / Decimal("100")
    player.critical = min(Decimal("0.500"), trait_critical + job.critical_bonus)
    player.hp = min(player.hp, player.max_hp)
    player.mp = min(player.mp, player.max_mp)
    return player


def set_development_player_state(player, *, target_level, target_job, target_hp, traits=None):
    if not 1 <= target_level <= 99:
        raise ValidationError("等級必須介於 1 至 99。")
    traits = traits or {field: getattr(player, field) for field in TRAIT_FIELDS}
    for field in TRAIT_FIELDS:
        value = traits[field]
        if not 1 <= value <= 99:
            raise ValidationError("角色特性必須介於 1 至 99。")
        setattr(player, field, value)
    player.level = target_level
    player.job = target_job
    recalculate_player_stats(player)
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
        if field == "weapon" and player.job.allowed_weapon_types and item.weapon_type not in player.job.allowed_weapon_types:
            raise ValidationError("目前職業不能使用此武器類型。")
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


def _apply_level_ups(player, rng=None):
    rng = rng or random
    levels = []
    while player.level < 99 and player.exp >= exp_to_next_level(player.level):
        player.level += 1
        for field in TRAIT_FIELDS:
            if getattr(player, field) < 99 and rng.random() < TRAIT_GROWTH_RATE:
                setattr(player, field, getattr(player, field) + 1)
        levels.append(player.level)
    if levels:
        recalculate_player_stats(player)
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
    level_ups = _apply_level_ups(player, rng)
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
        "player_after": combat_unit_dict(player_combat_unit(player)),
        "monster_snapshot": combat_unit_dict(monster_snapshot),
        "rounds": outcome.rounds,
        "rewards": rewards,
    }
