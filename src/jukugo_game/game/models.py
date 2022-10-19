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

    @property
    def current_answerer_is_player(self) -> bool:
        return not self.game.answerer

    @property
    def result(self) -> str:
        if self.current_answerer_is_player:
            return "勝利"
        else:
            return "敗北"

    def get_is_done_from_player(self, **kwargs) -> None:
        player_set: _QS
        player: _A
        is_done: bool = False
        for name in ["player", "computer"]:
            player_set = getattr(self, name).all()
            player = player_set.last()
            is_done |= player.is_done
        return is_done

    def __get_update_dict(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = self.__dict__
        update_dict: Dict[str, Any] = {}
        for key in self.update_list:
            update_dict[key] = kwargs.get(key, None)
        return update_dict

    def increment(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.is_done = self.get_is_done_from_player(**kwargs)
        self.num_rally += 1
        self.answerer = not self.answerer
        update_args: Dict[str, Any] = self.__get_update_dict()
        Play.objects.filter(game_id=self.game_id).update(**update_args)

    def get_key_zip(self) -> zip:
        key_list: List[str] = list(self.change_dict.keys())
        key_id_list: List[int] = [self.key_list.index(k) for k in key_list]
        return zip(key_id_list, key_list)

    def process_val(self,
                    val: Tuple[Any, ...]) -> Tuple[Any, ...]:
        # zipはgeneratorなので使うごとに生成する必要がある
        key_zip: zip = self.get_key_zip()
        key_id: int
        key_name: str
        list_v: List[Any] = list(val)
        for key_id, key_name in key_zip:
            list_v[key_id] = self.change_dict[key_name](list_v[key_id])
        return tuple(list_v)

    def make_val_visualize(self, val_qs: _QS) -> List[Tuple[Any, ...]]:
        v: Tuple[Any, ...]
        output: List[Tuple[Any, ...]] = []
        for v in val_qs:
            v = self.process_val(v)
            output.append(v)
        return output

    def get_values_from_attr(self, attr: str) -> List[Tuple[Any, ...]]:
        value_set: _QS = getattr(self, attr).all()
        full_values: _QS[Tuple[Any, ...]] =\
            value_set.values_list(*self.key_list)
        processed_values: List[Tuple[Any, ...]] =\
            self.make_val_visualize(full_values)
        return [(attr, *info) for info in processed_values]

    def get_jukugo_list_by_players(self) -> List[str]:
        jukugo_list: Dict[str, List[str]] = {}
        for name in ["player", "computer"]:
            jukugo_list[name] = self.get_values_from_attr(name)
        return jukugo_list

    def switch_player(self, player: str = "computer") -> str:
        if player == "computer":
            return "player"
        else:
            return "computer"

    def get_last_IDs(self,
                     word_dict: Dict[str, List[Any]],
                     method: Callable[..., int]
                     ) -> Tuple[int, int]:
        return method([len(v) for v in word_dict.values()])

    def push_word_recursively(self,
                              jukugo_dict: Dict[str, List[Tuple[Any, ...]]],
                              max_id: int,
                              first: str = "computer",
                              count: int = 0,
                              word_list: List[Tuple[Any, ...]] = []
                              ):
        if count == max_id:
            word_list += [jukugo_dict[self.switch_player(first)][count]]
            return word_list

        if count == 0:
            word_list += [jukugo_dict[first][count]]
        else:
            word_list += [
                jukugo_dict[self.switch_player(first)][count],
                jukugo_dict[first][count]
            ]
        return self.push_word_recursively(jukugo_dict=jukugo_dict,
                                          max_id=max_id,
                                          first=first,
                                          count=count + 1,
                                          word_list=word_list
                                          )

    def get_jukugo_list(self,
                        first: str = "computer",
                        reverse: bool = False
                        ) -> List[Tuple[Any, ...]]:
        jukugo_dict: Dict[str, List[Tuple[Any, ...]]]
        jukugo_dict = self.get_jukugo_list_by_players()

        # Not specifying 'word_list',
        # the case that a same tables is concatenated below on html may happen.
        jukugo_list: List[Tuple[Any, ...]] = self.push_word_recursively(
            jukugo_dict=jukugo_dict,
            max_id=self.get_last_IDs(jukugo_dict, max) - 1,
            first=first,
            word_list=[]
        )

        if reverse:
            jukugo_list.reverse()
        return jukugo_list


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
