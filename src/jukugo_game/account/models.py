import uuid
from typing import Any, Dict, List, TypeVar

from django.contrib.auth import models as auth_models
from django.contrib.auth.models import User
from django.db import models
from game.models import Computer, Play, Player

_Q = TypeVar("_Q", bound=models.QuerySet)


class UserQuerySet(models.QuerySet):
    """ここでゲームは復元できないけどユーザーとゲーム回数を復元できる
    """

    def filter_by_pk(self, pk: int) -> _Q:
        """
        "Filter the queryset by the primary key."

        The first line of the docstring is a one sentence summary of the function.
        The next line is blank.
        The next line is a more detailed description of the function.
        The next line is blank. The next line is the type signature of the function

        Args:
          pk (int): The primary key of the object you want to retrieve.

        Returns:
          A QuerySet
        """
        return self.filter(pk=pk)


class SuperUserManager(auth_models.UserManager.from_queryset(UserQuerySet)):
    all_types: List[str] = ["play", "win", "lose"]

    def __getattribute__(self, __name: str) -> Any:
        """
        `__getattribute__` is a function that is called
        when you try to access an attribute of an object

        Args:
          __name (str): The name of the attribute being accessed.

        Returns:
          The super class of the class.
        """
        return super().__getattribute__(__name)

    def _check_type(self, count_type: str) -> bool:
        # It's checking if the count type is in the list of all types.
        return count_type in self.all_types

    def _get_context(self, obj: _Q, count_type: str) -> Dict[str, int]:
        """
        It takes a Django model object and a string,
        and returns a dictionary with the string as the key and
        the value of the model object's attribute
        with the same name as the string plus one

        Args:
          obj (_Q): _Q
          count_type (str): The name of the attribute that will be incremented.

        Returns:
          A dictionary with the key being the attribute name
          and the value being the attribute value.
        """
        attr_name: str = f"num_{count_type}"
        return {attr_name: int(getattr(obj, attr_name)) + 1}

    def increment(self, pk: int, count_type: str = "play") -> None:
        """
        "Increment the count of a given type for a given user."

        The first thing we do is check that the count type is valid.
        If it's not, we raise a `ValueError`

        Args:
          pk (int): The primary key of the user object.
          count_type (str): The type of count to increment. Defaults to play
        """
        if self._check_type(count_type):
            raise ValueError()

        # User object is uniquely defined by pk value.
        user: _Q = self.filter_by_pk(pk)
        context: Dict[str, int] = self._get_context(user, count_type)
        self.update(**context)


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

    objects = SuperUserManager()

    def increment(self, play: Play) -> None:
        cpu: Computer = play.cpu
        player: Player = play.user

        if cpu.is_done:
            self.num_lose += 1
        elif player.is_done:
            self.num_win += 1
        self.num_play += 1
