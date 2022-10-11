"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from account import views
from django.contrib import admin
from django.urls import include, path
from game import views as game_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.IndexView.as_view(), name="home"),
    # sign up
    path("signup/", views.SignupView.as_view(), name="signup"),
    # log out
    path("logout/", views.SuperLogoutView.as_view(), name="logout"),
    path("game/<int:pk>/", game_view.AccountView.as_view(), name="game_account"),
    path("game/", include("game.urls")),
    path("account/", include("account.urls")),
]
