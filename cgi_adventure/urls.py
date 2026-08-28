from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from game.views import DevelopmentLoginView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", DevelopmentLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include("game.urls")),
]
