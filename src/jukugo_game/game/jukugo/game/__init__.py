from typing import Any, Dict, Optional, TypeVar

from game.jukugo.questions.state import State

from .level import JukugoList
from .player import AbstractPlayer, GameMaster
from .player import LevelChangeableESPlayer as tmp

_A = TypeVar("_A", bound=AbstractPlayer)

JUKUGO_LIST: Dict[str, Any] = JukugoList()["kanjipedia"]
MASTER: GameMaster = GameMaster(JUKUGO_LIST, player_id=0, name="master")
DIFFICULTIES: Dict[str, tmp] = tmp.\
    create_all_computers(JUKUGO_LIST, player_id=0, name="computer")


def set_id(first: str = "computer", cpu_level: str = "normal") -> None:
    master_id: int = 0
    cpu_id: int = 0
    if first == "computer":
        master_id += 1
    else:
        cpu_id += 1
    MASTER.set_id(master_id)
    DIFFICULTIES[cpu_level].set_id(cpu_id)


# computerでもplayerでもリセットして初期熟語を削る
def first(
    first: str = "computer",
    cpu_level: str = "normal",
    jukugo: Optional[str] = None
) -> str:
    players: Dict[str, _A] = {
        "master": MASTER,
        "computer": DIFFICULTIES[cpu_level]
    }

    set_id(first=first, cpu_level=cpu_level)
    player: _A = players[first]
    player.env.reset(jukugo)

    for ap in players.values():
        ap.level.increase(player.env.state.obs["jukugo"])

    return player.env.state


# playerは熟語を入力するのでincreaseのみ、computerの熟語を返す
def next(cpu_level: str = "normal", jukugo: Optional[str] = None) -> State:
    if jukugo is None:
        raise ValueError()

    MASTER.level.increase(jukugo)
    computer: tmp = DIFFICULTIES[cpu_level]
    computer.env._step({"jukugo": jukugo})
    computer.level.increase(jukugo)

    return computer.env.state
