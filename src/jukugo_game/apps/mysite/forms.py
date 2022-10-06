from django import forms

from .models import Register


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Register
        app_label = "register"
        fields = (
            "date",
            "user_name",
        )
