import uuid

from django.contrib.auth.models import User
from django.db import models
from game.models import Computer, Play, Player


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
    play: models.Field = models.ManyToManyField(Play)

    class Meta:
        db_table: str = "account"

    def increment(self, play: Play) -> None:
        cpu: Computer = play.cpu
        player: Player = play.user

        if cpu.is_done:
            self.num_lose += 1
        elif player.is_done:
            self.num_win += 1
        self.num_play += 1

        self.save()
