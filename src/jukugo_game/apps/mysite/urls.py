from django.urls import path

from . import views

app_name = "register"
urlpatterns = [
    path("", views.IndexView.as_view(), name="register_index"),
    path("register/", views.RegisterCreateView.as_view(), name="register"),
    path(
        "register/complete/",
        views.RegisterCreateCompleteView.as_view(),
        name="register_complete",
    ),
    path("register/history", views.RegisterListView.as_view(), name="register_history"),
    path(
        "register/detail/<uuid:pk>/",
        views.RegisterDetailView.as_view(),
        name="register_detail",
    ),
]
