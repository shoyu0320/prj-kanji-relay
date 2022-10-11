from typing import Any, Dict

from django.urls import reverse_lazy

# Create your views here.
from django.views.generic import CreateView, ListView, TemplateView

from .forms import JukugoForm
from .models import Jukugo


class AccountView(TemplateView):
    template_name = "game/index.html"
    context_object_name = "game"
    model = Jukugo

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["author"] = "熟語リレーします"
        return context


class InputJukugoView(CreateView):
    template_name = "game/input_jukugo.html"
    form_class = JukugoForm
    model = Jukugo
    success_url = reverse_lazy("game:input_jukugo")
    context_object_name = "game"


class GameWinView(TemplateView):
    template_name = "game/game_win.html"
    model = Jukugo
    context_object_name = "game"


class GameLoseView(TemplateView):
    template_name = "game/game_lose.html"
    model = Jukugo
    context_object_name = "game"


class GameDetailView(ListView):
    template_name = "game/game_detail.html"
    model = Jukugo
    context_object_name = "game"
