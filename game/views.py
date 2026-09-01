import json

from django.conf import settings
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import DevelopmentAuthenticationForm, DevelopmentPlayerForm, PlayerCreateForm
from .line_identity import LineIdentityError, get_or_create_line_user, verify_line_id_token
from .models import Area, BattleRecord, EquipmentSet, GameAccount, Item, Job, Player, PlayerItem
from .services import BattleCooldown, apply_job_transition, available_job_transitions, run_battle, set_development_player_state


JOB_TRANSITION_COPY = {
    "金剛力士": "鋼鐵般的意志，以及一拳解決問題的決心",
    "飛燕劍客": "追不到的車尾燈，以及比風還快的劍影",
    "御靈師": "能和狐仙聊天、和紙人談工作的奇妙人脈",
    "方士": "一張符解決不了的事，那就再貼一張",
    "護法金剛": "你的拳頭已經不只是拳頭，而是一份需要蓋章的正義。下一步，你要把它升級成守護眾生的鐵腕，連蚊子都不敢靠近。",
    "流雲劍俠": "你的腳步快得讓影子開始申請加班。現在，是時候讓劍法也學會飄逸，踏雲而行。",
    "通幽使": "你和靈體相處得越來越融洽，甚至開始有人請你代收陰間包裹。下一步，你要成為出入幽冥如走後門的通幽使。",
    "五行術士": "你已經能讓金木水火土輪流替你加班。既然大家都這麼熟了，不如正式升任五行輪轉，讓符法不打烊。",
    "鎮獄神將": "你的威嚴已經重到連地府公文都不敢遲到。下一站，不是升官，是直接讓牢獄知道誰才是老闆，一戟鎮住地府十八層。",
    "凌霄劍仙": "你的劍快到連月光都來不及反射。凡間已經放不下你的劍鞘，現在你要飛升成為一劍凌霄、御風而行的劍仙。",
    "萬靈宗師": "從狐鬼精怪到路邊石頭，大家都想拜你為師。既然萬物都有求於你，那就正式接下這個稱號，一聲令下就能令萬靈排隊報到。",
    "乾坤天師": "你已經不只是在施法，而是在替天地重新排版。當乾坤開始聽你的安排，你唯一缺少的只是名片，做好準備接掌天地吧!",
}
JOB_CHOICE_INTRO = "你感覺身體充滿了能量。這股力量若不找個出口，恐怕連隔壁攤的豆腐都要遭殃。你想把這股能量轉化成："
JOB_TIER_GUIDE = {
    Job.Tier.SECOND: "你已經走過初入江湖的階段。這身功力若再不找個正經名分，恐怕連敵人都不知道該怎麼稱呼你。現在，你可以踏入更高一階的修行。",
    Job.Tier.THIRD: "你在凡間累積的功力已經多到快要超載。再往前一步，便不是升職，而是讓天地重新考慮規則。請做好準備，迎接最後一階的修行。",
}
JOB_SUCCESS_COPY = {
    Job.Tier.FIRST: "你的力量終於找到工作了。從今天起，你不再只是遊方客。",
    Job.Tier.SECOND: "你已經不是當年那個只會揮拳、揮劍、招靈或貼符的人了。新的職階，新的麻煩，也是一樣多的敵人。",
    Job.Tier.THIRD: "恭喜。你的修行已經超出一般人的理解範圍。請記得低調，尤其是在打穿屋頂之後。",
}


class DevelopmentLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = DevelopmentAuthenticationForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if settings.DEBUG:
            username = getattr(settings, "DEV_ADMIN_USERNAME", "")
            password = getattr(settings, "DEV_ADMIN_PASSWORD", "")
            if username and password:
                initial.update({"username": username, "password": password})
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["line_liff_id"] = settings.LINE_LIFF_ID
        context["line_login_enabled"] = bool(settings.LINE_LIFF_ID and settings.LINE_CHANNEL_ID)
        context["development_login_enabled"] = settings.DEBUG
        return context


@require_POST
def line_login(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "登入資料格式錯誤。"}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "登入資料格式錯誤。"}, status=400)

    try:
        identity = verify_line_id_token(
            payload.get("id_token"),
            settings.LINE_CHANNEL_ID,
        )
        user = get_or_create_line_user(identity)
    except LineIdentityError as error:
        return JsonResponse({"error": str(error)}, status=401)

    login(request, user)
    default_redirect_url = resolve_url(settings.LOGIN_REDIRECT_URL)
    redirect_url = payload.get("next") or default_redirect_url
    if not url_has_allowed_host_and_scheme(
        redirect_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_url = default_redirect_url
    return JsonResponse({"redirect_url": redirect_url})


def _get_player(user):
    try:
        return Player.objects.select_related("job", "equipment__weapon", "equipment__armor", "equipment__accessory").get(account__user=user)
    except Player.DoesNotExist:
        return None


def health(request):
    return HttpResponse("ok")


def _progression_redirect(player):
    if available_job_transitions(player).exists():
        return redirect("game:job_progression")
    return None


@login_required
def home(request):
    player = _get_player(request.user)
    if not player:
        return redirect("game:create_player")
    progression_redirect = _progression_redirect(player)
    if progression_redirect:
        return progression_redirect
    areas = Area.objects.filter(enabled=True, required_level__lte=player.level)
    if not settings.DEBUG:
        areas = areas.filter(is_level_simulation=False)
    areas = areas.order_by("required_level", "id")
    recent_battles = player.battles.order_by("-created_at")[:5]
    return render(request, "game/home.html", {
        "player": player,
        "areas": areas,
        "recent_battles": recent_battles,
        "development_player_form": DevelopmentPlayerForm(initial={
            "level": player.level,
            "job": player.job,
            "hp": player.hp,
        }) if settings.DEBUG else None,
        "job_skills": player.job.skills.filter(enabled=True).order_by("priority", "id"),
    })


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
    player = _get_player(request.user)
    progression_redirect = _progression_redirect(player)
    if progression_redirect:
        return progression_redirect
    return render(request, "game/battle_result.html", {"battle": result})


@login_required
def battle_history(request, battle_id):
    player = _get_player(request.user)
    if not player:
        return redirect("game:create_player")
    record = get_object_or_404(BattleRecord, pk=battle_id, player=player)
    battle = {
        "battle_id": record.pk,
        "random_seed": record.random_seed,
        "result": record.result,
        "end_reason": record.end_reason,
        "player_before": {"name": player.name},
        "monster_snapshot": record.monster_snapshot,
        "rounds": record.rounds,
        "rewards": record.rewards,
    }
    return render(request, "game/battle_result.html", {"battle": battle, "is_history": True})


@login_required
def job_progression(request):
    player = _get_player(request.user)
    if not player:
        return redirect("game:create_player")
    options = list(available_job_transitions(player))
    if not options:
        return redirect("game:home")
    if player.job.tier == Job.Tier.STARTER:
        for job in options:
            job.transition_copy = JOB_TRANSITION_COPY.get(job.name, "一條尚待命名的修行道路")
        return render(request, "game/job_choice.html", {"player": player, "jobs": options, "intro": JOB_CHOICE_INTRO})
    if len(options) != 1:
        raise ValidationError("進階職業路線設定不完整。")
    job = options[0]
    job.transition_copy = JOB_TRANSITION_COPY.get(job.name, "你的修行即將進入下一個階段。")
    return render(request, "game/job_transition_pending.html", {
        "player": player,
        "job": job,
        "guide": JOB_TIER_GUIDE.get(job.tier, "你的修行即將進入下一個階段。"),
    })


@login_required
@require_POST
@transaction.atomic
def job_transition(request):
    player = Player.objects.select_for_update().select_related("job").get(account__user=request.user)
    target_job = get_object_or_404(Job, pk=request.POST.get("job_id"), enabled=True)
    try:
        apply_job_transition(player, target_job)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("game:job_progression")
    return render(request, "game/job_transition_success.html", {
        "player": player,
        "job": target_job,
        "success_copy": JOB_SUCCESS_COPY.get(target_job.tier, "你的修行又向前了一步。"),
    })


@login_required
@require_POST
@transaction.atomic
def development_set_level(request):
    if not settings.DEBUG:
        raise Http404
    player = Player.objects.select_for_update().select_related("job").get(account__user=request.user)
    form = DevelopmentPlayerForm(request.POST)
    if not form.is_valid():
        messages.error(request, "開發角色資料格式不正確。")
        return redirect("game:home")
    try:
        set_development_player_state(
            player,
            target_level=form.cleaned_data["level"],
            target_job=form.cleaned_data["job"],
            target_hp=form.cleaned_data["hp"],
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("game:home")
    progression_redirect = _progression_redirect(player)
    if progression_redirect:
        return progression_redirect
    messages.success(request, "已更新角色的等級、職業與 HP，並同步能力值。")
    return redirect("game:home")


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
