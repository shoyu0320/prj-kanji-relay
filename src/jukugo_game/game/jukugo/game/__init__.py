from typing import Any, Dict, List, Optional, Tuple, TypeVar

from game.jukugo.game.level import JukugoList
from game.jukugo.game.player import DummyPlayer, LevelChangeableESPlayer
from game.jukugo.questions.variable_box import VariablesBox

_S = TypeVar("_S", bound=List[int])
_V = TypeVar("_V", bound=VariablesBox)


# 全員別々の辞書を持ってるので、すり合わせが必要
def create_game(
    username: str, order: int = 0, level: str = "normal",
    scope: Optional[_S] = None, mode: Optional[str] = None
) -> Tuple[DummyPlayer, LevelChangeableESPlayer]:

    jukugo_list: JukugoList = JukugoList(scope, mode)
    jukugos: Dict[str, Any] = jukugo_list.level["kanjipedia"]
    player: DummyPlayer = DummyPlayer(
        jukugos, player_id=order, name=username
    )
    cpu_order: int = (order + 1) % 2
    computer: LevelChangeableESPlayer = LevelChangeableESPlayer(
        jukugos, player_id=cpu_order, name="CPU", difficulty=level
    )

    return (player, computer)
