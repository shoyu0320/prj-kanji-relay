from typing import Tuple

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Model

from .models import SpecialUser


class SignupForm(UserCreationForm):
    class Meta:
        model: Model = SpecialUser
        fields: Tuple[str, ...] = (
            "username",
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    class Meta:
        model: Model = SpecialUser
        fields: Tuple[str, ...] = ("username", "password")

