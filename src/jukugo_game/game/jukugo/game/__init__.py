from typing import Dict, List, Optional, TypeVar

from game.jukugo.questions.variable_box import VariablesBox

from .level import JukugoList
from .player import AbstractPlayer, GameMaster
from .player import LevelChangeableESPlayer as tmp

_S = TypeVar("_S", bound=List[int])
_V = TypeVar("_V", bound=VariablesBox)

JUKUGO_LIST: JukugoList = JukugoList()["kanjipedia"]
MASTER: GameMaster = GameMaster(JUKUGO_LIST, player_id=0, name="master")


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
    players: Dict[str, AbstractPlayer] = {
        "master": MASTER,
        "computer": DIFFICULTIES[cpu_level]
    }

    player: AbstractPlayer = players[inputs]
    player.env.reset(jukugo)

    for ap in players.values():
        ap.level.increase(player.env.state.obs["jukugo"])

    return player.env.state


# playerは熟語を入力するのでincreaseのみ、computerの熟語を返す
def next(cpu_level: str = "normal", jukugo: Optional[str] = None):
    if jukugo is None:
        raise ValueError()

    MASTER.level.increase(jukugo)
    computer: tmp = DIFFICULTIES[cpu_level]
    computer.env._step({"jukugo": jukugo})
    computer.level.increase(jukugo)

    return computer.env.state
