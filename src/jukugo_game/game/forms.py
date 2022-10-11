from django import forms

from .models import Jukugo


class JukugoForm(forms.ModelForm):
    class Meta:
        model = Jukugo
        app_label = "game"
        fields = ("jukugo",)
