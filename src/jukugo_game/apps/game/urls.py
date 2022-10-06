from django.urls import path

from . import views

app_name = "game"
urlpatterns = [
    path("account/", views.AccountView.as_view(), name="account"),
    path("game/<uuid:pk>/", views.InputJukugoView.as_view(), name="input_jukugo"),
    path("game/win/", views.GameWinView.as_view(), name="game_win",),
    path("game/lose/", views.GameLoseView.as_view(), name="game_lose"),
    path("game/detail/", views.GameDetailView.as_view(), name="game_detail",),
]
