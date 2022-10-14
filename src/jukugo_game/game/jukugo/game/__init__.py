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


def get_computer_difficulties() -> Dict[str, tmp]:
    difficulties: Dict[str, int] = {
        "master": 1.0,
        "hard": 0.8,
        "normal": 0.5,
        "easy": 0.2,
    }
    return {
        d: tmp(
            JUKUGO_LIST,
            player_id=0,
            name="computer",
            difficulty=r
        ) for d ,r in difficulties.items()
    }


DIFFICULTIES: Dict[str, tmp] = get_computer_difficulties()


# computerでもplayerでもリセットして初期熟語を削る
def first(
    inputs: str = "computer",
    cpu_level: str = "normal",
    jukugo: Optional[str] = None
) -> str:
    players: Dict[str, _A] = {
        "master": MASTER,
        "computer": DIFFICULTIES[cpu_level]
    }

    player: AbstractPlayer = players[inputs]
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
