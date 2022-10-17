from typing import Any, Dict, Optional, Tuple, TypeVar

from account.models import SpecialUser
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
# Create your views here.
from django.views.generic import ListView, TemplateView

from .forms import JukugoForm, LevelChoiceForm
from .jukugo.main import first, step, write
from .jukugo.questions.state import State
from .models import Computer, Play, Player

_M = TypeVar("_M", bound=models.Model)
_O = TypeVar("_O", bound=models.Manager)
_P = TypeVar("_P", bound=Player)
_C = TypeVar("_C", bound=Computer)


class GameStartView(TemplateView):
    template_name: str = "game/game_start.html"
    context_object_name: str = "play"
    model = Play

    @property
    def account(self) -> _O:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    @property
    def current_game(self) -> Optional[_O]:
        account: _O = self.account
        return account.play.last()

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
        game: _M = Play.\
            create_game(cpu_level=level, start_jukugo=start_state.obs["jukugo"])
        account: _O = self.account
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
    model: Play = Play

    players: Dict[str, _M] = {
        "player": Player,
        "computer": Computer
    }
    name_map: Dict[str, str] = {
        "player": "user",
        "computer": "cpu"
    }

    @property
    def account(self) -> _O:
        pk: str = self.kwargs["pk"]
        account: _O = SpecialUser.objects.get(pk=pk)
        return account

    @property
    def current_game(self) -> Optional[_O]:
        account: _O = self.account
        return account.play.last()

    @property
    def num_rally(self) -> int:
        game: _P = self.current_game
        return int(game.num_rally)

    @property
    def current_answerer_is_player(self) -> bool:
        game: _P = self.current_game
        return game.answerer

    def step_game(self, request: HttpRequest, form: JukugoForm) -> bool:
        game: _P = self.current_game

        # playerを更新
        given_jukugo: str = request.POST.get("jukugo")
        cpu_level: str = self.kwargs["level"]
        state: State

        for name in ["player", "computer"]:
            if "computer" in name:
                state = step(name, cpu_level)
                given_jukugo = state.obs["jukugo"]
            state = write(given_jukugo, name, cpu_level)
            player = self.players[name](is_done=state.done, **state.obs)
            player.save()
            game.increment(**{self.name_map[name]: player}, **state.obs)
            given_jukugo = state.obs["jukugo"]
            if game.is_done:
                return True

        return False

    def _get_attrs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"pk": self.request.user.pk}
        # TODO 便宜上最後のユーザーを取り出してるけど、セキュアにはIDで取り出すのが良さそう(OBJECT.get(id=specified_id))
        last_obj: Optional[_O] = Computer.objects.last()
        level: str = last_obj.level
        if level is not None:
            kwargs.update(level=level)
        return kwargs

    def redirect(self) -> HttpResponseRedirect:
        url: str = self.get_success_url()
        return redirect(url)

    def get_success_url(self) -> str:
        kwargs: Dict[str, Any] = self._get_attrs()
        url: str = self.get_end_url()
        return reverse(url, kwargs=kwargs)

    def get_end_url(self) -> str:
        if self.current_answerer_is_player:
            return "game:win"
        else:
            return "game:lose"

    def _post(self, request: HttpRequest) -> None:
        form: JukugoForm = JukugoForm(request.POST)
        is_done: bool = False
        if form.is_valid():
            is_done = self.step_game(request, form)

        return is_done

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        context: Dict[str.Any] = {}
        is_done: bool = False
        if request.method == "POST":
            is_done = self._post(request)
            context.update(
                current=self._get_jukugo_form(),
                last=self._get_last_jukugo(),
                num_rally=self.num_rally
            )

        # 初期値=Noneを回避する
        if (is_done) and (self.num_rally > 0):
            return self.redirect()
        else:
            return render(request, self.template_name, context)

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
