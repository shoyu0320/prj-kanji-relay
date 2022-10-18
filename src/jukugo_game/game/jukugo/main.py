from typing import Any, Dict, Optional, TypeVar

from game.jukugo.game.level import JukugoList
from game.jukugo.game.player import AbstractPlayer, GameMaster
from game.jukugo.game.player import LevelChangeableESPlayer as tmp
from game.jukugo.questions.state import State

_A = TypeVar("_A", bound=AbstractPlayer)

ALL_JUKUGO: Dict[str, Any] = JukugoList().level["kanjipedia"]
MASTER: _A = GameMaster(ALL_JUKUGO, player_id=0, name="master")
PLAYER: _A = GameMaster(ALL_JUKUGO, player_id=1, name="player")
DIFFICULTIES: Dict[str, tmp] = tmp.\
    create_all_computers(ALL_JUKUGO, player_id=0, name="computer")


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
        "player": PLAYER,
        "computer": DIFFICULTIES[cpu_level]
    }


def reset_dict(cpu_level: str = "normal", jukugo: Optional[str] = None) -> None:
    players: Dict[str, _A] = get_players(cpu_level)
    for ap in players.values():
        ap.reset()


def update_dict(
    cpu_level: str = "normal",
    jukugo: Optional[str] = None,
) -> None:
    """
    It takes a string of CPU levels, a jukugo, and a boolean, and it steps the players

    Args:
      cpu_level (str): str = "normal". Defaults to normal
      jukugo (Optional[str]): The jukugo to be used for the level increase.
      If None, a random jukugo will be used.
      on_first (bool): If True, the player's level will be reset to 1. Defaults to False
    """
    players: Dict[str, _A] = get_players(cpu_level)
    for ap in players.values():
        ap.level.increase(jukugo)


def reflect_state(
    state: State,
    player_name: str = "computer",
    cpu_level: str = "normal"
    ) -> None:
    players: Dict[str, _A] = get_players(cpu_level)
    k: str
    v: _A

    for k, v in players.items():
        if k == player_name:
            continue
        v.env.set_previous_state(state)


def get_updated_state(player: _A, player_name: str = "computer", cpu_level: str = "normal", has_jukugo: bool = True) -> State:
    state: State = player.env.state
    if has_jukugo:
        # 辞書更新は全体
        update_dict(cpu_level, state)
        reflect_state(state, player_name, cpu_level)
    player.env.set_new_state_without_obs()
    return player.env.state


def write(jukugo: str,
          player_name: str = "computer",
          cpu_level: str = "normal"
          ) -> State:
    player: _A = get_players(cpu_level=cpu_level)[player_name]
    # stateを作っただけで更新はしてない
    player.env.set_new_observation(jukugo=jukugo)
    has_jukugo: bool = jukugo is not None

    return get_updated_state(player, player_name, cpu_level, has_jukugo)


def step(player_name: str = "computer", cpu_level: str = "normal") -> State:
    player: _A = get_players(cpu_level=cpu_level)[player_name]

    # 観測更新は対象プレイヤーのみ/checkerの順で更新する
    new_jukugo: str = player.env._step()

    return new_jukugo


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
    reset_dict(cpu_level, jukugo)
    # リセット後の状態を使う
    state: State = player.env.state
    update_dict(cpu_level, state.obs["jukugo"])
    reflect_state(state, first, cpu_level)
    player.env.set_new_state_without_obs()

    return player.env.state
