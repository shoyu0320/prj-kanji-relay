import uuid
from typing import Optional, TypeVar

from django.db import models

_M = TypeVar("_M", bound=models.Model)
_F = TypeVar("_F", bound=models.Field)
_P = TypeVar("_P", bound="Play")
_A = TypeVar("_A", bound="AbstractGamePlayer")


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
    is_done: _F = models.BooleanField(verbose_name="勝ち負け", null=True, max_length=10)

    @classmethod

    def create_player(cls, *args, **kwargs) -> _A:
        player: _A = cls(**kwargs)
        player.save()


class Computer(AbstractGamePlayer):
    # 相手の難易度もついでに書いとく
    level: _F = models.CharField(
        verbose_name="難易度", default="normal", null=True, max_length=10
    )

    class Meta:
        db_table: str = "play_cpu"


class Player(AbstractGamePlayer):

    class Meta:
        db_table = "play_user"


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
        player: _A = Player()
        computer: _A = Computer(jukugo=start_jukugo, level=cpu_level)
        game: _P = cls(cpu=computer, user=player, jukugo=start_jukugo)
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
        self.save()
