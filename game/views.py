from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DevelopmentAuthenticationForm, PlayerCreateForm
from .models import Area, EquipmentSet, GameAccount, Item, Job, Player, PlayerItem
from .services import BattleCooldown, run_battle


class DevelopmentLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = DevelopmentAuthenticationForm

    def get_initial(self):
        initial = super().get_initial()
        if settings.DEBUG:
            username = getattr(settings, "DEV_ADMIN_USERNAME", "")
            password = getattr(settings, "DEV_ADMIN_PASSWORD", "")
            if username and password:
                initial.update({"username": username, "password": password})
        return initial


def _get_player(user):
    try:
        return Player.objects.select_related("job", "equipment__weapon", "equipment__armor", "equipment__accessory").get(account__user=user)
    except Player.DoesNotExist:
        return None


@login_required
def home(request):
    player = _get_player(request.user)
    if not player:
        return redirect("game:create_player")
    areas = Area.objects.filter(enabled=True, required_level__lte=player.level).order_by("required_level", "id")
    recent_battles = player.battles.order_by("-created_at")[:5]
    return render(request, "game/home.html", {"player": player, "areas": areas, "recent_battles": recent_battles})


@login_required
@transaction.atomic
def create_player(request):
    if _get_player(request.user):
        return redirect("game:home")
    form = PlayerCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        account, _ = GameAccount.objects.get_or_create(user=request.user)
        job = Job.objects.filter(enabled=True, required_level=1).order_by("id").first()
        if not job:
            form.add_error(None, "遊戲資料尚未初始化，請聯絡管理者。")
        else:
            player = form.save(commit=False)
            player.account = account
            player.job = job
            player.save()
            equipment = EquipmentSet.objects.create(player=player)
            starter_weapon = Item.objects.filter(name="桃木劍", item_type=Item.Type.WEAPON).first()
            if starter_weapon:
                PlayerItem.objects.create(player=player, item=starter_weapon, quantity=1)
                equipment.weapon = starter_weapon
                equipment.save(update_fields=["weapon"])
            messages.success(request, "角色建立完成，冒險開始！")
            return redirect("game:home")
    return render(request, "game/create_player.html", {"form": form})


@login_required
@require_POST
def battle(request, area_id):
    try:
        result = run_battle(user=request.user, area_id=area_id)
    except Area.DoesNotExist:
        raise Http404
    except (BattleCooldown, PermissionDenied, ValidationError) as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, "messages") else str(exc))
        return redirect("game:home")
    return render(request, "game/battle_result.html", {"battle": result})


@login_required
def inventory(request):
    player = _get_player(request.user)
    if not player:
        return redirect("game:create_player")
    items = player.inventory.select_related("item").order_by("item__item_type", "item__name")
    return render(request, "game/inventory.html", {"player": player, "items": items})


@login_required
@require_POST
@transaction.atomic
def equip(request, player_item_id):
    player = Player.objects.select_for_update().get(account__user=request.user)
    player_item = get_object_or_404(PlayerItem.objects.select_related("item"), pk=player_item_id, player=player, quantity__gt=0)
    item = player_item.item
    field = {Item.Type.WEAPON: "weapon", Item.Type.ARMOR: "armor", Item.Type.ACCESSORY: "accessory"}.get(item.item_type)
    if not field:
        messages.error(request, "這個物品不能裝備。")
    else:
        equipment, _ = EquipmentSet.objects.select_for_update().get_or_create(player=player)
        setattr(equipment, field, item)
        equipment.save(update_fields=[field])
        messages.success(request, "已裝備「{}」。".format(item.name))
    return redirect("game:inventory")


def leaderboard(request):
    players = Player.objects.select_related("job").order_by("-job_count", "-level", "-exp", "id")[:100]
    return render(request, "game/leaderboard.html", {"players": players})
