from typing import Any, Dict, Optional, Tuple, TypeVar

from account.models import SpecialUser
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
# Create your views here.
from django.views.generic import ListView, TemplateView

from .forms import JukugoForm, LevelChoiceForm
from .jukugo.main import first, next, set_player_state
from .jukugo.questions.state import State
from .models import Computer, Play, Player

_M = TypeVar("_M", bound=models.Model)
_O = TypeVar("_O", bound=models.Manager)
_P = TypeVar("_P", bound=Player)
_C = TypeVar("_C", bound=Computer)


class GameStartView(TemplateView):
    template_name: str = "game/game_start.html"
    context_object_name: str = "level"

    @property
    def account(self) -> SpecialUser:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    def _get_url(self, kwargs: Dict[str, Any]) -> str:
        if self._level_defined(kwargs):
            return "game:play"
        else:
            return "game:start"

    def _level_defined(self, kwargs: Dict[str, Any]) -> bool:
        return "level" in kwargs

    def _get_attrs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"pk": self.request.user.pk}
        # TODO 便宜上最後のユーザーを取り出してるけど、セキュアにはIDで取り出すのが良さそう(OBJECT.get(id=specified_id))
        last_obj: Optional[_O] = Computer.objects.last()
        level: str = last_obj.level
        if level is not None:
            kwargs.update(level=level)
        return kwargs

    def get_success_url(self) -> str:
        kwargs: Dict[str, Any] = self._get_attrs()
        url: str = self._get_url(kwargs)
        return reverse(url, kwargs=kwargs)

    def get(
        self, request: HttpRequest, *args: Tuple[Any, ...], **kwargs: Dict[str, Any]
    ) -> HttpResponse:
        # これでプルダウン型のレベル調整を可能にする
        form: LevelChoiceForm = LevelChoiceForm()
        context: Dict[str, LevelChoiceForm] = {"level": form}
        return render(request, self.template_name, context)

    def create_game(self, request: HttpRequest, form: LevelChoiceForm) -> None:
        # post の name 属性で絞り込み
        selected_level: str = request.POST.get("level")
        # これ綺麗な書き方ありそうだけど知らない
        level: str = form.get_name(selected_level)
        # form経由でなく、modelから直接セーブする方が好き
        start_state: State = first(first="computer", cpu_level=level, jukugo=None)
        game: _M = Play.create_game(cpu_level=level, start_jukugo=start_state.obs["jukugo"])
        account: _M = self.account
        account.play.add(game)

    def redirect(self) -> HttpResponseRedirect:
        url: str = self.get_success_url()
        return redirect(url)

    def _post(self, request: HttpRequest) -> None:
        form: LevelChoiceForm = LevelChoiceForm(request.POST)
        if form.is_valid():
            # オブジェクトの保存
            self.create_game(request, form)

    def post(
        self, request: HttpRequest, *args: Tuple[Any, ...], **kwargs: Dict[str, Any]
    ) -> HttpResponseRedirect:
        if request.method == "POST":
            self._post(request)
        # 保存したらURL作ってリダイレクトが直感的で楽
        # formタグ内のbuttonタグからリダイレクトってどうするんじゃろ
        return self.redirect()


class GamePlayView(TemplateView):
    template_name: str = "game/game_play.html"
    context_object_name: str = "play"
    # model: Play = Play
    # form_class: JukugoForm = JukugoForm

    def is_bad_jukugo(self, jukugo: str) -> bool:
        # ルールに則ってない熟語ならTrue
        return False

    def declare_lose(self, request: HttpRequest) -> bool:
        # 負け宣言したらTrue
        return False

    def is_finished(self, request: HttpRequest, jukugo: str) -> bool:
        vj: bool = self.is_bad_jukugo(jukugo)
        dl: bool = self.declare_lose(request)
        return vj | dl

    @property
    def account(self) -> _O:
        pk: str = self.kwargs["pk"]
        account: _O = SpecialUser.objects.get(pk=pk)
        return account

    @property
    def current_game(self) -> Optional[_O]:
        account: _O = self.account
        return account.play.last()

    def step_game(self, request: HttpRequest, form: JukugoForm) -> bool:
        game: _M = self.current_game

        # playerを更新
        submitted_jukugo: str = request.POST.get("jukugo")
        player_state: State = set_player_state(submitted_jukugo)
        state: bool = self.is_finished(request, submitted_jukugo)

        player_state.set_obs({"state": ((not state) | (not player_state.done))})
        player: _P = Player(**player_state.obs)
        player.save()

        game.increment(user=player, **player_state.obs)

        if not game.state:
            return True

        # computerを更新
        next_state: State = next(cpu_level=self.kwargs["level"], state=player_state)

        next_state.set_obs({"state": (not next_state.done)})
        computer: _C = Computer(**next_state.obs)
        computer.save()

        game.increment(cpu=computer, **next_state.obs)

        if not game.state:
            return True

        return False

    def get_end_url(self) -> str:
        return ""

    def _post(self, request: HttpRequest) -> None:
        form: JukugoForm = JukugoForm(request.POST)
        is_done: bool = False
        if form.is_valid():
            is_done = self.step_game(request, form)

        if is_done:
            url: str = self.get_end_url()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        context: Dict[str.Any] = {}
        if request.method == "POST":
            self._post(request)
            context.update(current=self._get_jukugo_form())
            context.update(last=self._get_last_jukugo())

        return render(request, self.template_name, context)

    def redirect(self) -> HttpResponseRedirect:
        url: str = self.get_success_url()
        return redirect(url)

    def get_success_url(self) -> str:
        return reverse("game:play", kwargs=self.kwargs)

    def _get_jukugo_form(self) -> JukugoForm:
        # 熟語の入力フォームを作る
        return JukugoForm()

    def _get_last_jukugo(self) -> str:
        # 直前の相手の熟語を取得する
        game: _O = self.current_game
        if game is not None:
            last: Optional[_O] = game.jukugo
            return last
        else:
            return "熟語"


class GameWinView(TemplateView):
    template_name = "game/game_win.html"
    model = Player
    context_object_name = "player"


class GameLoseView(TemplateView):
    template_name = "game/game_lose.html"
    model = Player
    context_object_name = "player"


class GameDetailView(ListView):
    template_name = "game/game_detail.html"
    model = Play
    context_object_name = "play"
