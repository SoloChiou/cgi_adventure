from django.urls import path

from . import views


app_name = "game"
urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.home, name="home"),
    path("players/new/", views.create_player, name="create_player"),
    path("jobs/progression/", views.job_progression, name="job_progression"),
    path("jobs/transition/", views.job_transition, name="job_transition"),
    path("development/level/", views.development_set_level, name="development_set_level"),
    path("areas/<int:area_id>/battle/", views.battle, name="battle"),
    path("battles/<int:battle_id>/", views.battle_history, name="battle_history"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/<int:player_item_id>/equip/", views.equip, name="equip"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
