from django.urls import reverse_lazy

# Create your views here.
from django.views.generic import CreateView, ListView, TemplateView

from .forms import JukugoForm
from .models import Jukugo


class AccountView(TemplateView):
    template_name = "jukugo/index.html"
    context_object_name = "account"


class InputJukugoView(CreateView):
    template_name = "jukugo/input_jukugo.html"
    form_class = JukugoForm
    model = Jukugo
    success_url = reverse_lazy("account:input_jukugo")
    context_object_name = "input"


class GameWinView(TemplateView):
    template_name = "jukugo/game_win.html"
    model = Jukugo
    context_object_name = "win"


class GameLoseView(TemplateView):
    template_name = "jukugo/game_lose.html"
    model = Jukugo
    context_object_name = "lose"


class GameDetailView(ListView):
    template_name = "jukugo/game_detail.html"
    model = Jukugo
    context_object_name = "detail"
