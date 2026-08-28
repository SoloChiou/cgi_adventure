from django.urls import path

from . import views


app_name = "game"
urlpatterns = [
    path("", views.home, name="home"),
    path("players/new/", views.create_player, name="create_player"),
    path("areas/<int:area_id>/battle/", views.battle, name="battle"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/<int:player_item_id>/equip/", views.equip, name="equip"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
