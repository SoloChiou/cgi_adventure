from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .domain import exp_to_next_level
from .line_identity import LineIdentityError, get_or_create_line_user, verify_line_id_token
from .models import Area, BattleRecord, EquipmentSet, GameAccount, Item, Job, Player, PlayerItem
from .services import BattleCooldown, TRAIT_FIELDS, apply_job_transition, available_job_transitions, job_requirements_met, recalculate_player_stats, run_battle, set_development_player_state, validate_initial_traits


def health(request):
    return HttpResponse("ok")


def _user_data(request, api_token=None):
    user = request.user
    data = {"authenticated": user.is_authenticated, "user": {"id": user.pk, "username": user.username} if user.is_authenticated else None, "csrf_token": get_token(request)}
    if api_token:
        data["api_token"] = api_token
    return data


def _player_data(player):
    if not player:
        return None
    equipment = getattr(player, "equipment", None)
    next_level_exp = exp_to_next_level(player.level) if player.level < 99 else None
    title = next((row for row in player.job.titles.all() if row.min_level <= player.level <= row.max_level), None)
    return {
        "id": player.pk, "name": player.name, "level": player.level, "exp": player.exp,
        "next_level_exp": next_level_exp,
        "gold": player.gold,
        "hp": player.hp, "mp": player.mp, "max_hp": player.max_hp, "max_mp": player.max_mp,
        "atk": player.atk, "defense": player.defense, "intelligence": player.intelligence,
        "magic_defense": player.magic_defense, "agility": player.agility, "critical": float(player.critical),
        "traits": {
            "strength": player.strength, "intellect": player.intellect, "piety": player.piety,
            "vitality": player.vitality, "dexterity": player.dexterity,
            "speed": player.speed, "charisma": player.charisma,
        },
        "job_count": player.job_count, "job": {"id": player.job_id, "name": player.job.name, "name_en": player.job.name_en, "tier": player.job.tier},
        "title": ({"name": title.name, "name_en": title.name_en, "rank": title.rank, "min_level": title.min_level, "max_level": title.max_level} if title else None),
        "equipment": {slot: ({"id": item.pk, "name": item.name} if item else None) for slot, item in (
            ("weapon", equipment.weapon), ("armor", equipment.armor), ("accessory", equipment.accessory)
        )} if equipment else {"weapon": None, "armor": None, "accessory": None},
        "skills": [{"id": skill.pk, "name": skill.name, "name_en": skill.name_en, "mp_cost": skill.mp_cost} for skill in player.job.skills.filter(enabled=True).order_by("priority", "id")],
    }


def _current_player(user):
    return Player.objects.select_related("job", "equipment__weapon", "equipment__armor", "equipment__accessory").prefetch_related("job__titles").filter(account__user=user).first()


def _error(exc, response_status=status.HTTP_400_BAD_REQUEST):
    message = exc.messages[0] if isinstance(exc, ValidationError) and exc.messages else str(exc)
    return Response({"detail": message}, status=response_status)


class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(_user_data(request))


class LineLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        origin = request.headers.get("Origin", "").rstrip("/")
        allowed_origins = {value.rstrip("/") for value in settings.CORS_ALLOWED_ORIGINS}
        if not origin or origin not in allowed_origins:
            return Response({"detail": "LINE 登入來源無效。"}, status=status.HTTP_403_FORBIDDEN)
        id_token = request.data.get("id_token", "")
        if not isinstance(id_token, str) or not id_token.strip():
            return Response({"detail": "缺少 LINE ID token。"}, status=status.HTTP_400_BAD_REQUEST)
        context = request.data.get("channel_context", "mini_app")
        if context not in ("mini_app", "web"):
            return Response({"detail": "LINE 登入來源無效。"}, status=status.HTTP_400_BAD_REQUEST)
        channel_ids = {"mini_app": settings.LINE_CHANNEL_ID, "web": settings.LINE_WEB_CHANNEL_ID}
        channel_id = channel_ids[context]
        if not channel_id:
            return Response({"detail": "LINE 登入尚未完成設定。"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            identity = verify_line_id_token(id_token, channel_id)
            user = get_or_create_line_user(identity)
        except LineIdentityError:
            return Response({"detail": "LINE 登入憑證無效。"}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        token, _ = Token.objects.get_or_create(user=user)
        return Response(_user_data(request, token.key))


class DevLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not settings.ENABLE_DEV_LOGIN or not settings.DEV_ADMIN_USERNAME:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        user = get_object_or_404(get_user_model(), username=settings.DEV_ADMIN_USERNAME, is_active=True)
        token, _ = Token.objects.get_or_create(user=user)
        request.user = user
        return Response(_user_data(request, token.key))


class LogoutView(APIView):
    def post(self, request):
        if isinstance(request.auth, Token):
            request.auth.delete()
        logout(request)
        return Response({"authenticated": False, "user": None})


class GameStateView(APIView):
    def get(self, request):
        player = _current_player(request.user)
        areas = Area.objects.filter(enabled=True).order_by("required_level", "id")
        development_jobs = []
        if not settings.DEBUG:
            areas = areas.filter(is_level_simulation=False)
        else:
            development_jobs = [
                {"id": job.pk, "name": job.name, "name_en": job.name_en, "tier": job.tier}
                for job in Job.objects.filter(enabled=True).order_by("tier", "id")
            ]
        recent = player.battles.order_by("-created_at")[:5] if player else []
        return Response({
            "player": _player_data(player),
            "areas": [{"id": row.pk, "name": row.name, "description": row.description, "required_level": row.required_level, "cooldown_seconds": row.cooldown_seconds, "is_level_simulation": row.is_level_simulation} for row in areas],
            "recent_battles": [{
                "id": row.pk, "result": row.result,
                "monster_name": row.monster_snapshot.get("name", "未知妖物"),
                "monster_name_en": row.monster_snapshot.get("name_en", "Unknown Monster"),
                "created_at": row.created_at,
            } for row in recent],
            "job_transition_available": bool(player and available_job_transitions(player).exists()),
            "development_controls": settings.DEBUG,
            "development_jobs": development_jobs,
            "creation_jobs": [{
                "id": job.pk, "name": job.name, "name_en": job.name_en,
                "requirements": {field: getattr(job, "required_{}".format(field)) for field in TRAIT_FIELDS},
            } for job in Job.objects.filter(enabled=True, tier=Job.Tier.FIRST).order_by("id")] if not player else [],
        })


class PlayerCreateView(APIView):
    def post(self, request):
        if Player.objects.filter(account__user=request.user).exists():
            return Response({"detail": "角色已存在。"}, status=status.HTTP_409_CONFLICT)
        name = str(request.data.get("name", "")).strip()
        if not name or len(name) > 20:
            return Response({"detail": "角色名稱必須為 1 至 20 個字元。"}, status=status.HTTP_400_BAD_REQUEST)
        starter = get_object_or_404(Job, tier=Job.Tier.STARTER, enabled=True)
        try:
            traits = validate_initial_traits(request.data.get("traits"))
            target_job = Job.objects.get(pk=request.data.get("job_id"), enabled=True, tier=Job.Tier.FIRST, prerequisite_job=starter)
            if not job_requirements_met(target_job, traits):
                raise ValidationError("角色特性尚未符合此職業門檻。")
        except (Job.DoesNotExist, ValidationError) as exc:
            return _error(exc)
        account, _ = GameAccount.objects.get_or_create(user=request.user)
        player = Player.objects.create(account=account, name=name, job=target_job, job_count=1, **traits)
        recalculate_player_stats(player)
        player.save()
        EquipmentSet.objects.create(player=player)
        return Response(_player_data(player), status=status.HTTP_201_CREATED)


class JobProgressionView(APIView):
    def get(self, request):
        player = get_object_or_404(Player.objects.select_related("job"), account__user=request.user)
        available_jobs = list(available_job_transitions(player))
        available_ids = {job.pk for job in available_jobs}
        all_jobs = Job.objects.filter(enabled=True, tier=Job.Tier.FIRST).order_by("id")
        return Response({"player": _player_data(_current_player(request.user)), "jobs": [{
            "id": row.pk, "name": row.name, "name_en": row.name_en,
            "requirements": {field: getattr(row, "required_{}".format(field)) for field in TRAIT_FIELDS},
        } for row in available_jobs], "all_jobs": [{
            "id": row.pk, "name": row.name, "name_en": row.name_en,
            "requirements": {field: getattr(row, "required_{}".format(field)) for field in TRAIT_FIELDS},
            "eligible": row.pk in available_ids,
            "is_current": row.pk == player.job_id,
        } for row in all_jobs]})


class JobTransitionView(APIView):
    @transaction.atomic
    def post(self, request):
        player = get_object_or_404(Player.objects.select_for_update().select_related("job"), account__user=request.user)
        target = get_object_or_404(Job, pk=request.data.get("job_id"), enabled=True)
        try:
            apply_job_transition(player, target)
        except ValidationError as exc:
            return _error(exc)
        return Response(_player_data(_current_player(request.user)))


class DevelopmentPlayerView(APIView):
    def patch(self, request):
        if not settings.DEBUG:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        player = get_object_or_404(Player.objects.select_related("job"), account__user=request.user)
        try:
            target = Job.objects.get(pk=int(request.data.get("job_id", player.job_id)), enabled=True)
            raw_traits = request.data.get("traits", {})
            traits = {field: int(raw_traits.get(field, getattr(player, field))) for field in (
                "strength", "intellect", "piety", "vitality", "dexterity", "speed", "charisma"
            )}
            set_development_player_state(player, target_level=int(request.data.get("level", player.level)), target_job=target, target_hp=int(request.data.get("hp", player.hp)), traits=traits)
        except (AttributeError, Job.DoesNotExist, TypeError, ValueError, ValidationError) as exc:
            return _error(exc)
        return Response(_player_data(_current_player(request.user)))


class BattleView(APIView):
    def post(self, request, area_id):
        try:
            return Response(run_battle(user=request.user, area_id=area_id))
        except Area.DoesNotExist:
            return Response({"detail": "找不到地區。"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as exc:
            return _error(exc, status.HTTP_403_FORBIDDEN)
        except (BattleCooldown, ValidationError) as exc:
            return _error(exc)


class BattleHistoryView(APIView):
    def get(self, request, battle_id):
        row = get_object_or_404(BattleRecord, pk=battle_id, player__account__user=request.user)
        from .battle_narrative import BattleNarrativeComposer
        composer = BattleNarrativeComposer(row.random_seed)
        return Response({"battle_id": row.pk, "random_seed": row.random_seed, "result": row.result, "end_reason": row.end_reason, "monster_snapshot": row.monster_snapshot, "rounds": row.rounds, "narratives": {"zh-TW": composer.compose(row.rounds, "zh-TW"), "en": composer.compose(row.rounds, "en")}, "rewards": row.rewards, "created_at": row.created_at})


class InventoryView(APIView):
    def get(self, request):
        player = get_object_or_404(Player, account__user=request.user)
        rows = PlayerItem.objects.filter(player=player).select_related("item").order_by("item__item_type", "item__name")
        return Response({"player": _player_data(_current_player(request.user)), "items": [{"id": row.pk, "quantity": row.quantity, "item": {"id": row.item_id, "name": row.item.name, "type": row.item.item_type, "rarity": row.item.rarity, "atk_bonus": row.item.atk_bonus, "defense_bonus": row.item.defense_bonus, "agility_bonus": row.item.agility_bonus}} for row in rows]})


class EquipView(APIView):
    @transaction.atomic
    def post(self, request, player_item_id):
        row = get_object_or_404(PlayerItem.objects.select_related("item", "player__job"), pk=player_item_id, player__account__user=request.user, quantity__gt=0)
        if row.item.item_type == Item.Type.MATERIAL:
            return Response({"detail": "材料不能裝備。"}, status=status.HTTP_400_BAD_REQUEST)
        if row.item.item_type == Item.Type.WEAPON and row.player.job.allowed_weapon_types and row.item.weapon_type not in row.player.job.allowed_weapon_types:
            return Response({"detail": "目前職業不能使用此武器類型。"}, status=status.HTTP_400_BAD_REQUEST)
        equipment, _ = EquipmentSet.objects.select_for_update().get_or_create(player=row.player)
        setattr(equipment, row.item.item_type, row.item)
        equipment.save(update_fields=[row.item.item_type])
        return Response(_player_data(_current_player(request.user)))


class LeaderboardView(APIView):
    def get(self, request):
        rows = Player.objects.select_related("job").prefetch_related("job__titles").order_by("-job_count", "-level", "-exp", "id")[:100]
        result = []
        for index, row in enumerate(rows, 1):
            title = next((item for item in row.job.titles.all() if item.min_level <= row.level <= item.max_level), None)
            result.append({
                "rank": index, "name": row.name,
                "job": {"name": row.job.name, "name_en": row.job.name_en},
                "title": {"name": title.name, "name_en": title.name_en, "rank": title.rank} if title else None,
                "job_count": row.job_count, "level": row.level, "exp": row.exp,
            })
        return Response(result)
