from typing import Any, Callable

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, SignupForm
from .models import SpecialUser


class IndexView(TemplateView):
    template_name: str = "account/index.html"
    form_class: ModelForm = SignupForm
    model = SpecialUser
    context_object_name = "player"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["player"] = self.request.user
        return context


class SignupView(CreateView):
    template_name: str = "account/signup.html"
    form_class: ModelForm = SignupForm
    success_url: Callable[[str], Any] = reverse_lazy("account:user")

    def form_valid(self, form):
        result = super().form_valid(form)
        user = self.object
        login(self.request, user)
        return result


class SuperLoginView(LoginView):
    template_name: str = "account/login.html"
    form_class: ModelForm = LoginForm


class SuperLogoutView(LogoutView):
    template_name: str = "account/logout.html"


class SuperUserView(LoginRequiredMixin, TemplateView):
    template_name: str = "account/user.html"
    success_url: Callable[[str], Any] = reverse_lazy("account:user")
    context_object_name = "player"
    model = SpecialUser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["player"] = self.request.user
        return context


class GuestView(LoginRequiredMixin, TemplateView):
    template_name: str = "account/guest.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = SpecialUser.objects.exclude(
            username=self.request.user.username
        )
        return context
