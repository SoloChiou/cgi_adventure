from django.urls import path

from . import views


app_name = "game"
urlpatterns = [
    path("health/", views.health, name="health"),
    path("auth/session/", views.SessionView.as_view(), name="auth_session"),
    path("auth/line/", views.LineLoginView.as_view(), name="line_login"),
    path("auth/dev/", views.DevLoginView.as_view(), name="dev_login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("game/", views.GameStateView.as_view(), name="game_state"),
    path("players/", views.PlayerCreateView.as_view(), name="create_player"),
    path("jobs/progression/", views.JobProgressionView.as_view(), name="job_progression"),
    path("jobs/transition/", views.JobTransitionView.as_view(), name="job_transition"),
    path("development/player/", views.DevelopmentPlayerView.as_view(), name="development_player"),
    path("areas/<int:area_id>/battle/", views.BattleView.as_view(), name="battle"),
    path("battles/<int:battle_id>/", views.BattleHistoryView.as_view(), name="battle_history"),
    path("inventory/", views.InventoryView.as_view(), name="inventory"),
    path("inventory/<int:player_item_id>/equip/", views.EquipView.as_view(), name="equip"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
]
