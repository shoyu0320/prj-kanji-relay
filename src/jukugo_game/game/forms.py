from typing import Tuple

from django import forms

from .models import Computer, Player


class JukugoForm(forms.ModelForm):
    class Meta:
        model = Player
        app_label = "game"
        fields = ("jukugo",)


class LevelChoiceForm(forms.Form):
    choices: Tuple[Tuple[str, str], ...] = (
        (1, "easy"),
        (2, "normal"),
        (3, "hard"),
        (4, "master"),
    )
    level = forms.fields.ChoiceField(
        choices=choices,
        initial=2,
        required=True,
        label="難易度",
        widget=forms.Select(attrs={"class": "form-control", "id": "difficulty"}),
    )

    class Meta:
        model = Computer
        app_label = "game"
        fields = ("level",)

    def get_name(self, choice: str = 1):
        items = self.choices
        for k, v in items:
            if int(choice) == k:
                return v
