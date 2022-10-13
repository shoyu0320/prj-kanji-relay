from django.urls import path

from . import views

app_name = "game"
urlpatterns = [
    path("", views.GameStartView.as_view(), name="start"),
    path("<str:level>/", views.GamePlayView.as_view(), name="play"),
    path("win/", views.GameWinView.as_view(), name="win",),
    path("lose/", views.GameLoseView.as_view(), name="lose"),
    path("detail/", views.GameDetailView.as_view(), name="detail",),
]
