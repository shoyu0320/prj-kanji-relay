from typing import Any, Dict, List, Optional, Tuple, TypeVar

from account.models import SpecialUser
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

# Create your views here.
from django.views.generic import ListView, TemplateView

from .forms import JukugoForm, LevelChoiceForm
from .jukugo.main import first, get_comment, get_unused_jukugo, step, write
from .jukugo.questions.state import State
from .models import AbstractGamePlayer, Computer, Play, Player

_A = TypeVar("_A", bound=AbstractGamePlayer)
_QS = TypeVar("_QS", bound=QuerySet)


class GameStartView(TemplateView):
    template_name: str = "game/game_start.html"
    context_object_name: str = "play"
    model = Play

    @property
    def account(self) -> SpecialUser:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    @property
    def current_game(self) -> Optional[_A]:
        account: SpecialUser = self.account
        games: _QS = account.play.all()
        return games.last()

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
        level: str = self.current_game.level
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
        # これでプルダウン型のレベル調整を可能にする <- いらない
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
        Play.create_game(
            account=self.account,
            cpu_level=level,
            start_jukugo=start_state.obs["jukugo"],
        )

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

    players: Dict[str, _A] = {"player": Player, "computer": Computer}

    @property
    def account(self) -> SpecialUser:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    @property
    def current_game(self) -> Optional[_A]:
        account: SpecialUser = self.account
        games: _QS = account.play.all()
        return games.last()

    @property
    def num_rally(self) -> int:
        game: Play = self.current_game
        return int(game.num_rally)

    @property
    def current_answerer_is_player(self) -> bool:
        game: Play = self.current_game
        return not game.answerer

    def step_game(self, request: HttpRequest, form: JukugoForm) -> bool:
        game: Play = self.current_game

        # playerを更新
        given_jukugo: str = request.POST.get("jukugo")
        cpu_level: str = self.kwargs["level"]
        state: State
        kwargs: Dict[str, Any] = {}

        for name in ["player", "computer"]:
            if "computer" in name:
                given_jukugo = step(name, cpu_level)
                kwargs.update(level=cpu_level)
            state = write(given_jukugo, name, cpu_level)
            kwargs.update(game=game, is_done=state.done)
            player: _A = self.players[name](**kwargs, **state.obs)
            player.save(force_insert=True)
            game.increment(**state.obs)
            given_jukugo = state.obs["jukugo"]
            if game.is_done:
                return True
            kwargs = {}

        return False

    def _get_attrs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"pk": self.request.user.pk}
        level: str = self.current_game.level
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
        self.account.increment()
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
                num_rally=self.num_rally,
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
        game: Play = self.current_game
        if game is not None:
            last: Optional[str] = game.jukugo
            return last
        else:
            return "熟語"


class GameResultView(ListView):
    class Meta:
        abstract = True

    @property
    def account(self) -> SpecialUser:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    @property
    def current_game(self) -> Optional[_A]:
        account: SpecialUser = self.account
        games: _QS = account.play.all()
        return games.last()

    @property
    def defeat_player(self) -> str:
        game: Play = self.current_game
        if game.result == "勝利":
            return "computer"
        else:
            return "player"

    @property
    def defeat_comment(self) -> List[str]:
        defeat: str = self.defeat_player
        cpu_level: str = self.current_game.level
        return get_comment(defeat, cpu_level)

    @property
    def available_jukugo(self) -> List[str]:
        game: Play = self.current_game
        last_jukugo: str = game.computer.all().last().jukugo
        if last_jukugo is None:
            last_jukugo = game.player.all().last().jukugo
        level: str = game.level
        return get_unused_jukugo(
            player="player", cpu_level=level, last_jukugo=last_jukugo
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        game: Play = self.current_game
        context["jukugo_list"] = game.get_jukugo_list()
        context["available_list"] = self.available_jukugo
        context["comments"] = self.defeat_comment
        return context


class GameWinView(GameResultView):
    template_name = "game/game_win.html"
    model = Play
    context_object_name = "play"


class GameLoseView(GameResultView):
    template_name = "game/game_lose.html"
    model = Play
    context_object_name = "play"


class GameDetailView(ListView):
    template_name = "game/game_detail.html"
    model = Play
    context_object_name = "play"
    success_url: str = reverse_lazy("game:detail")

    @property
    def account(self) -> SpecialUser:
        pk: int = self.kwargs["pk"]
        return SpecialUser.objects.get(pk=pk)

    @property
    def all_games(self) -> Optional[_QS]:
        account: SpecialUser = self.account
        return account.play.all()

    @property
    def current_game(self) -> Optional[_A]:
        games: _QS = self.all_games
        return games.last()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        all_games: Play = self.all_games
        context["game_list"] = [
            (game.pk, game.result, game.num_rally, game.level, game.get_jukugo_list())
            for game in all_games
        ]
        return context
