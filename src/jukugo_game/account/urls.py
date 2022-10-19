from django.urls import path

from . import views

app_name = "account"
urlpatterns = [
    # log in
    path("", views.SuperLoginView.as_view(), name="login"),
    path("user_id=<int:pk>/", views.SuperUserView.as_view(), name="user"),
]
