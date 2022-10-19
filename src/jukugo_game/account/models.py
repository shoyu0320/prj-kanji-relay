import uuid
from typing import Dict, TypeVar

from django.contrib.auth.models import User
from django.db import models

_T = TypeVar("_T", bound=models.Model)
_QS = TypeVar("_QS", bound=models.QuerySet)


class SpecialUser(User):
    special_id: models.Field = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )
    num_win: models.Field = models.PositiveIntegerField(default=0, verbose_name="勝利数")
    num_lose: models.Field = models.PositiveBigIntegerField(
        default=0, verbose_name="敗北数"
    )
    num_play: models.Field = models.PositiveBigIntegerField(
        default=0, verbose_name="試合数"
    )

    class Meta:
        db_table: str = "account"

    @property
    def current_game(self) -> _T:
        game: _QS = self.play.all()
        return game.last()

    def increment(self) -> None:
        game: _T = self.current_game
        player_set: _QS
        player: _T
        is_done_dict: Dict[str, bool] = {}
        for name in ["player", "computer"]:
            player_set = getattr(game, name).all()
            player: _T = player_set.last()
            is_done_dict[name] = player.is_done

        if is_done_dict["computer"]:
            self.num_lose += 1
        elif is_done_dict["player"]:
            self.num_win += 1
        self.num_play += 1

        self.save(force_update=True)
