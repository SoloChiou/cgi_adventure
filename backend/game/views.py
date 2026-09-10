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

from .line_identity import LineIdentityError, get_or_create_line_user, verify_line_id_token
from .models import Area, BattleRecord, EquipmentSet, GameAccount, Item, Job, Player, PlayerItem
from .services import BattleCooldown, apply_job_transition, available_job_transitions, run_battle, set_development_player_state


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
    return {
        "id": player.pk, "name": player.name, "level": player.level, "exp": player.exp, "gold": player.gold,
        "hp": player.hp, "mp": player.mp, "max_hp": player.max_hp, "max_mp": player.max_mp,
        "atk": player.atk, "defense": player.defense, "intelligence": player.intelligence,
        "magic_defense": player.magic_defense, "agility": player.agility, "critical": float(player.critical),
        "job_count": player.job_count, "job": {"id": player.job_id, "name": player.job.name, "tier": player.job.tier},
        "equipment": {slot: ({"id": item.pk, "name": item.name} if item else None) for slot, item in (
            ("weapon", equipment.weapon), ("armor", equipment.armor), ("accessory", equipment.accessory)
        )} if equipment else {"weapon": None, "armor": None, "accessory": None},
        "skills": [{"id": skill.pk, "name": skill.name, "mp_cost": skill.mp_cost} for skill in player.job.skills.filter(enabled=True).order_by("priority", "id")],
    }


def _current_player(user):
    return Player.objects.select_related("job", "equipment__weapon", "equipment__armor", "equipment__accessory").filter(account__user=user).first()


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
        if not settings.LINE_CHANNEL_ID:
            return Response({"detail": "LINE 登入尚未完成設定。"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            identity = verify_line_id_token(id_token, settings.LINE_CHANNEL_ID)
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
        if not settings.DEBUG:
            areas = areas.filter(is_level_simulation=False)
        recent = player.battles.order_by("-created_at")[:5] if player else []
        return Response({
            "player": _player_data(player),
            "areas": [{"id": row.pk, "name": row.name, "description": row.description, "required_level": row.required_level, "cooldown_seconds": row.cooldown_seconds, "is_level_simulation": row.is_level_simulation} for row in areas],
            "recent_battles": [{"id": row.pk, "result": row.result, "monster_name": row.monster_snapshot.get("name", "未知妖物"), "created_at": row.created_at} for row in recent],
            "job_transition_available": bool(player and available_job_transitions(player).exists()),
            "development_controls": settings.DEBUG,
        })


class PlayerCreateView(APIView):
    def post(self, request):
        if Player.objects.filter(account__user=request.user).exists():
            return Response({"detail": "角色已存在。"}, status=status.HTTP_409_CONFLICT)
        name = str(request.data.get("name", "")).strip()
        if not name or len(name) > 20:
            return Response({"detail": "角色名稱必須為 1 至 20 個字元。"}, status=status.HTTP_400_BAD_REQUEST)
        starter = get_object_or_404(Job, tier=Job.Tier.STARTER, enabled=True)
        account, _ = GameAccount.objects.get_or_create(user=request.user)
        player = Player.objects.create(account=account, name=name, job=starter)
        EquipmentSet.objects.create(player=player)
        return Response(_player_data(player), status=status.HTTP_201_CREATED)


class JobProgressionView(APIView):
    def get(self, request):
        player = get_object_or_404(Player.objects.select_related("job"), account__user=request.user)
        return Response({"player": _player_data(_current_player(request.user)), "jobs": [{"id": row.pk, "name": row.name, "tier": row.tier, "required_level": row.required_level} for row in available_job_transitions(player)]})


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
            set_development_player_state(player, target_level=int(request.data.get("level", player.level)), target_job=target, target_hp=int(request.data.get("hp", player.hp)))
        except (Job.DoesNotExist, TypeError, ValueError, ValidationError) as exc:
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
        return Response({"battle_id": row.pk, "random_seed": row.random_seed, "result": row.result, "end_reason": row.end_reason, "monster_snapshot": row.monster_snapshot, "rounds": row.rounds, "rewards": row.rewards, "created_at": row.created_at})


class InventoryView(APIView):
    def get(self, request):
        player = get_object_or_404(Player, account__user=request.user)
        rows = PlayerItem.objects.filter(player=player).select_related("item").order_by("item__item_type", "item__name")
        return Response({"player": _player_data(_current_player(request.user)), "items": [{"id": row.pk, "quantity": row.quantity, "item": {"id": row.item_id, "name": row.item.name, "type": row.item.item_type, "rarity": row.item.rarity, "atk_bonus": row.item.atk_bonus, "defense_bonus": row.item.defense_bonus, "agility_bonus": row.item.agility_bonus}} for row in rows]})


class EquipView(APIView):
    @transaction.atomic
    def post(self, request, player_item_id):
        row = get_object_or_404(PlayerItem.objects.select_related("item", "player"), pk=player_item_id, player__account__user=request.user, quantity__gt=0)
        if row.item.item_type == Item.Type.MATERIAL:
            return Response({"detail": "材料不能裝備。"}, status=status.HTTP_400_BAD_REQUEST)
        equipment, _ = EquipmentSet.objects.select_for_update().get_or_create(player=row.player)
        setattr(equipment, row.item.item_type, row.item)
        equipment.save(update_fields=[row.item.item_type])
        return Response(_player_data(_current_player(request.user)))


class LeaderboardView(APIView):
    def get(self, request):
        rows = Player.objects.select_related("job").order_by("-job_count", "-level", "-exp", "id")[:100]
        return Response([{"rank": index, "name": row.name, "job": row.job.name, "job_count": row.job_count, "level": row.level, "exp": row.exp} for index, row in enumerate(rows, 1)])
