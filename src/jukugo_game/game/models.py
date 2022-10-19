import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from account.models import SpecialUser
from django.db import models
from django.db.models import QuerySet

_F = TypeVar("_F", bound=models.Field)
_P = TypeVar("_P", bound="Play")
_A = TypeVar("_A", bound="AbstractGamePlayer")
_QS = TypeVar("_QS", bound=QuerySet)


class Play(models.Model):
    """試合に関する情報を載せていくDB
        試合ごとに熟語のリレー情報や勝ち負けを入れていく
    """
    update_list: List[str] = [
        "answerer", "jukugo", "jukugo_id", "yomi", "num_rally", "is_done"
    ]
    # TODO: Add both 'jukugo_id' and yomi in a displaying key as well.
    key_list: List[str] = [
        "jukugo", "is_done"
    ]
    change_dict: Dict[str, Any] = {
        "is_done": lambda d: "x" if d else "o"
    }

    @classmethod
    def create_game(
        cls,
        account: SpecialUser,
        cpu_level: str = "normal",
        start_jukugo: Optional[str] = None
    ) -> _P:
        game: _P = cls(account=account, level=cpu_level, jukugo=start_jukugo)
        game.save(force_insert=True)
        player: _A = Player(game=game)
        player.save(force_insert=True)
        computer: _A = Computer(game=game, level=cpu_level, jukugo=start_jukugo)
        computer.save(force_insert=True)
        return game

    account = models.ForeignKey(
        SpecialUser, on_delete=models.CASCADE, related_name='play')
    game_id: _F = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )
    # 相手の難易度もついでに書いとく
    level: _F = models.CharField(
        verbose_name="難易度", default="normal", max_length=10
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
    is_done = models.BooleanField(verbose_name="試合終了", default=False)

    class Meta:
        db_table: str = "play"

    def get_is_done_from_player(self, **kwargs) -> None:
        player: Optional[_A] = kwargs.get("user", None) or kwargs.get("cpu", None)
        for name in ["user", "cpu"]:
            player = player or kwargs.get(name)
        return player.is_done

    def increment(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.is_done = self.get_is_done_from_player(**kwargs)
        self.num_rally += 1
        self.answerer = not self.answerer

# makemigrations, migrate はいらないものが入らないように、migrations内を消しつつ進めること
# こいつがデータベースの中身を決める
class AbstractGamePlayer(models.Model):
    jukugo: _F = models.CharField(
        verbose_name="熟語", default=None, null=True, max_length=10
    )
    jukugo_id: _F = models.IntegerField(
        verbose_name="熟語ID", default=None, null=True
    )
    yomi: _F = models.CharField(
        verbose_name="読み", default=None, null=True, max_length=20
    )
    # 継続状態:False/負け状態:True(次の熟語が出てこない;None)/その他:Null
    is_done: _F = models.BooleanField(
        verbose_name="勝ち負け", default=False, null=True, max_length=10
    )

    class Meta:
        abstract = True

    @classmethod
    def create_player(cls, *args, **kwargs) -> _A:
        player: _A = cls(*args, **kwargs)
        player.save()


class Computer(AbstractGamePlayer):
    game: _F = models.ForeignKey(
        Play, verbose_name="ゲーム", on_delete=models.CASCADE, related_name='computer'
    )
    # 相手の難易度もついでに書いとく
    level: _F = models.CharField(
        verbose_name="難易度", default="normal", max_length=10
    )
    cpu_id: _F = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )

    class Meta:
        db_table: str = "computer"


class Player(AbstractGamePlayer):
    game: _F = models.ForeignKey(
        Play, verbose_name="ゲーム", on_delete=models.CASCADE, related_name='player'
    )
    user_id: _F = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )

    class Meta:
        db_table = "player"
