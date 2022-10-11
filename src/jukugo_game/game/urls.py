from django.urls import path

from . import views

app_name = "game"
urlpatterns = [
    path("account/", views.AccountView.as_view(), name="account"),
    path(
        "account/<uuid:pk>/jukugo_game/",
        views.InputJukugoView.as_view(),
        name="input_jukugo",
    ),
    path("win/", views.GameWinView.as_view(), name="game_win",),
    path("lose/", views.GameLoseView.as_view(), name="game_lose"),
    path("detail/", views.GameDetailView.as_view(), name="game_detail",),
]
