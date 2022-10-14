from typing import Any, Dict, Optional, TypeVar

from game.jukugo.game.level import JukugoList
from game.jukugo.game.player import AbstractPlayer, GameMaster
from game.jukugo.game.player import LevelChangeableESPlayer as tmp
from game.jukugo.questions.state import State

_A = TypeVar("_A", bound=AbstractPlayer)

JUKUGO_LIST: Dict[str, Any] = JukugoList().level["kanjipedia"]
MASTER: _A = GameMaster(JUKUGO_LIST, player_id=0, name="master")
DIFFICULTIES: Dict[str, tmp] = tmp.\
    create_all_computers(JUKUGO_LIST, player_id=0, name="computer")


def set_id(first: str = "computer", cpu_level: str = "normal") -> None:
    """
    `set_id` sets the id of the master and cpu based on the first player and cpu level

    Args:
      first (str): str = "computer". Defaults to computer
      cpu_level (str): The difficulty of the computer. Defaults to normal
    """
    master_id: int = 0
    cpu_id: int = 0
    if first == "computer":
        master_id += 1
    else:
        cpu_id += 1
    MASTER.set_id(master_id)
    DIFFICULTIES[cpu_level].set_id(cpu_id)


def get_players(cpu_level: str = "normal") -> Dict[str, _A]:
    """
    It returns a dictionary of players, where the keys are "master" and "computer",
    and the values are the players themselves

    Args:
        cpu_level (str): The difficulty of the computer player. Defaults to normal

    Returns:
        A dictionary with two keys, "master" and "computer",
        and two values, MASTER and DIFFICULTIES[cpu_level].
    """
    return {
        "master": MASTER,
        "computer": DIFFICULTIES[cpu_level]
    }


def step_players(
    cpu_levels: str = "normal",
    jukugo: Optional[str] = None,
    on_first: bool = False
) -> None:
    """
    It takes a string of CPU levels, a jukugo, and a boolean, and it steps the players

    Args:
      cpu_levels (str): str = "normal". Defaults to normal
      jukugo (Optional[str]): The jukugo to be used for the level increase. If None, a random jukugo
    will be used.
      on_first (bool): If True, the player's level will be reset to 1. Defaults to False
    """
    players: Dict[str, _A] = get_players(cpu_levels)
    for ap in players.values():
        if on_first:
            ap.reset()
        ap.level.increase(jukugo)


def set_player_state(jukugo: Optional[str] = None) -> State:
    if jukugo is None:
        raise ValueError()
    MASTER.env._set_new_state(jukugo)
    MASTER.level.increase(jukugo)
    return MASTER.env.state


# computerでもplayerでもリセットして初期熟語を与える
# TODO firstはgame:start時点で呼ぶ
def first(
    first: str = "computer",
    cpu_level: str = "normal",
    jukugo: Optional[str] = None
) -> str:
    """
    `first` is a function that returns the initial state of the game

    Args:
        first (str): The player who will make the first move. Defaults to computer
        cpu_level (str): The level of the computer. Defaults to normal
        jukugo (Optional[str]): The jukugo to start with.
            If None, a random jukugo will be chosen.

    Returns:
        The state of the game.
    """
    players: Dict[str, _A] = get_players(cpu_level=cpu_level)

    # TODO idのセットが一回で全てに適用されるのか気になる
    set_id(first=first, cpu_level=cpu_level)
    player: _A = players[first]
    player.env.reset(jukugo)
    step_players(cpu_level, player.env.state.obs["jukugo"], on_first=True)

    return player.env.state


# playerは熟語を入力するのでincreaseのみ、computerの熟語を返す
# TODO nextはgame:playで使う
def next(cpu_level: str = "normal", state: Optional[State] = None) -> State:
    if state is None:
        return None

    # step env (give jukugo) -> set states -> increase level
    computer: tmp = DIFFICULTIES[cpu_level]
    # step env -> set states -> increase level
    computer.env._step(state.obs)
    step_players(cpu_level, computer.env.state.obs["jukugo"])

    return computer.env.state
