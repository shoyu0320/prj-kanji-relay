import uuid
from typing import Optional, TypeVar
from uuid import UUID

from django.db import models

_M = TypeVar("_M", bound=models.Model)
_O = TypeVar("_O", bound=models.Manager)
_F = TypeVar("_F", bound=models.Field)
_Q = TypeVar("_Q", bound=models.QuerySet)
_P = TypeVar("_P", bound="Play")


# makemigrations, migrate はいらないものが入らないように、migrations内を消しつつ進めること
# こいつがデータベースの中身を決める
class Computer(models.Model):
    jukugo: _F = models.CharField(
        verbose_name="熟語", default=None, null=True, max_length=10
    )
    jukugo_id: _F = models.IntegerField(
        verbose_name="熟語ID", default=None, null=True
    )
    yomi: _F = models.CharField(
        verbose_name="読み", default=None, null=True, max_length=20
    )
    # 継続状態:True/負け状態:False(次の熟語が出てこない;None)/その他:Null
    state: _F = models.BooleanField(verbose_name="勝ち負け", null=True, max_length=10)
    # 相手の難易度もついでに書いとく
    level: _F = models.CharField(
        verbose_name="難易度", default="normal", null=True, max_length=10
    )

    class Meta:
        db_table: str = "play_cpu"


class Player(models.Model):
    jukugo: _F = models.CharField(
        verbose_name="熟語", default=None, null=True, max_length=10
    )
    jukugo_id: _F = models.IntegerField(
        verbose_name="熟語ID", default=None, null=True
    )
    yomi: _F = models.CharField(
        verbose_name="読み", default=None, null=True, max_length=20
    )
    # 継続状態:True/負け状態:False(次の熟語が出てこないなど;None)/その他:Null
    state: _F = models.BooleanField(verbose_name="勝ち負け", null=True)
    lose: _F = models.BooleanField(verbose_name="負け宣言", default=False)

    class Meta:
        db_table = "play_user"


class GameQuerySet(models.QuerySet):
    def filter_game_id(self, game_id: int) -> _Q:
        return self.filter(game_id=game_id)


class GameManager(models.Manager.from_queryset(GameQuerySet)):
    def increment(self, game_id: UUID, jukugo: str, state: bool) -> None:
        obj = self.filter_game_id(game_id=game_id)
        _ans: bool = self._change_answerer(obj)
        _num: int = self._increase_rally(obj)
        _stt: bool = self._judge_state(obj, state)
        _jkg: str = jukugo
        self.update(answerer=_ans, jukugo=_jkg, num_rally=_num, state=_stt)

    def _change_answerer(self, obj: _O) -> None:
        _ans: bool = obj.answerer
        return not _ans

    def _increase_rally(self, obj: _O) -> int:
        _num: int = obj.num_rally
        return _num + 1

    def _judge_state(self, obj: _O, declare: bool) -> bool:
        state: bool = obj.state
        return state | declare


class Play(models.Model):
    """試合に関する情報を載せていくDB
        試合ごとに熟語のリレー情報や勝ち負けを入れていく
    """
    @classmethod
    def create_game(
        cls,
        cpu_level: str = "normal",
        start_jukugo: Optional[str] = None
    ) -> _P:
        player: _M = Player()
        computer: _M = Computer(jukugo=start_jukugo, level=cpu_level)
        game: _M = cls(cpu=computer, user=player, jukugo=start_jukugo)
        _: _M
        for _ in [player, computer, game]:
            _.save()
        return game

    game_id: _F = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )

    # CPU の解答情報
    cpu: _F = models.OneToOneField(
        Computer, on_delete=models.CASCADE, verbose_name="CPU", related_name="cpu",
    )
    # プレイヤーの解答情報
    user: _F = models.OneToOneField(
        Player, on_delete=models.CASCADE, verbose_name="プレイヤー", related_name="user",
    )
    # 相手:False/自分:True(複数対戦を許可しない)
    answerer: _F = models.BooleanField(verbose_name="解答者", default=False)
    # (相手)->(自分)->(相手)->...
    jukugo: _F = models.CharField(
        verbose_name="リレーした熟語", null=True, default=None, max_length=10
    )
    jukugo_id: _F = models.IntegerField(
        verbose_name="熟語ID", default=None, null=True
    )
    yomi: _F = models.CharField(
        verbose_name="読み", default=None, null=True, max_length=20
    )
    num_rally: _F = models.PositiveIntegerField(verbose_name="ラリー回数", default=0)
    # 続く:False/最後:True
    state = models.BooleanField(verbose_name="試合終了", default=False)

    class Meta:
        db_table: str = "play"

    objects: _O = GameManager()

    def increment(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.num_rally += 1
        self.answerer = not self.answerer
        self.save()
