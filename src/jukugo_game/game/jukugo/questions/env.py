import os
from typing import Any, Dict, List, Optional, Union

import numpy as np
import yaml

# TODO runnerクラス、チェッカークラス（熟語の部分一致など）、
src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")

from questions.state import State
from questions.variable_box import VariablesBox
from utils.logger import GameLogger


class Env:
    def __init__(self) -> None:
        self.state: State = State()

    def reset(self) -> State:
        pass

    def step(self, obs: Dict[str, str]) -> State:
        raise NotImplementedError()


class JukugoRelayEnv(Env):
    def __init__(
        self,
        jukugo_list: List[str] = [],
        user_id: int = 0,
        user_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.jukugo_box: VariablesBox
        if isinstance(jukugo_list, VariablesBox):
            self.jukugo_box = jukugo_list
        else:
            self.jukugo_box = VariablesBox(jukugo_list, box_id=user_name)
        self.user_id: int = user_id
        self.user_name: Optional[str] = user_name

    def _get_unused_jukugo(self) -> List[Union[int, str]]:
        return self.jukugo_box.get_named_unused_vars(self.user_name)

    def _get_partial_match_jukugo(
        self, unused_jukugo: List[str], pre_jukugo: Optional[str] = None
    ) -> List[str]:
        jukugo_part: str = pre_jukugo[self.user_id]
        return [j for j in unused_jukugo if jukugo_part == j[self.user_id]]

    def _get_user_dependent_jukugo(
        self, unused_jukugo: List[str], pre_jukugo: Optional[str] = None
    ) -> List[str]:
        if pre_jukugo is None:
            return unused_jukugo
        else:
            return self._get_partial_match_jukugo(unused_jukugo, pre_jukugo)

    def _get_available_jukugo(self, pre_jukugo: Optional[str] = None) -> List[str]:
        unused_jukugo: List[str] = self._get_unused_jukugo()
        unused_jukugo = self._get_user_dependent_jukugo(unused_jukugo, pre_jukugo)
        return unused_jukugo

    def _get_new_jukugo(self, pre_jukugo: Optional[str] = None) -> Optional[str]:
        unused_jukugo: List[str] = self._get_available_jukugo(pre_jukugo)
        if len(unused_jukugo) > 0:
            jukugo = np.random.choice(unused_jukugo)
        else:
            jukugo = None
        return jukugo

    def _set_new_state(self, jukugo: str) -> None:
        judge: bool = self.jukugo_box.is_still_unused(jukugo)

        # 観測更新
        self.state.set_obs({"jukugo": jukugo})

        # 終端、報酬更新
        if jukugo is None:
            self.state.set_done(True)
            self.state.reward -= 1.0

        if not judge:
            self.state.reward -= 1.0

        # 情報更新
        unused: List[str] = self.jukugo_box.get_named_unused_vars(self.user_name)
        self.state.set_info({"unused_jukugo": unused, "is_in": judge})

    def reset(self, jukugos: Optional[Union[str, List[str]]] = None) -> Dict[str, str]:
        self.jukugo_box.reset()
        self.state.reset_std()

        # 初期状態の更新
        if isinstance(jukugos, str):
            self.jukugo_box.increase(jukugos)
        elif isinstance(jukugos, list):
            self.jukugo_box.increase_seq(jukugos)

        jukugo = self._get_new_jukugo()
        self._set_new_state(jukugo)
        return self.state

    def _step(self, obs: Dict[str, str]) -> State:
        # 受け取った熟語を使用済に
        old_jukugo: Optional[str] = obs.get("jukugo")
        self.jukugo_box.increase(old_jukugo)

        # 提出する熟語を使用済に
        new_jukugo: Optional[str] = self._get_new_jukugo(old_jukugo)
        self._set_new_state(new_jukugo)

        return new_jukugo

    def step(self, obs: Dict[str, str]) -> State:
        new_jukugo: str = self._step(obs)

        if new_jukugo is not None:
            self.jukugo_box.increase(new_jukugo)

        return self.state


def run():
    with open("../../data/niji-jukugo.yml") as f:
        data: List[str] = yaml.safe_load(f)

    # Set Variables
    i: int
    player: JukugoRelayEnv
    state: State
    epoch: int
    _: Any

    # Set Constant Values
    num_players: int = 4
    num_games: int = 20
    players: Dict[str, JukugoRelayEnv] = {}

    # logger
    logger: GameLogger = GameLogger()

    # Create Players
    for i in range(num_players):
        players[i] = JukugoRelayEnv(
            jukugo_dict=data, user_id=i % 2, user_name=f"プレイヤー{i}"
        )

    # Create and Run Games
    for game in range(1, num_games + 1):
        logger.log("game", (game,))

        # Initialize Constant
        epoch = 1

        # Reset Envs
        for i in range(num_players):
            state = players[i].reset()
        logger.log("continue", ("ゲームマスター", state.obs["jukugo"], False))

        # Start Game
        while not state.done:
            logger.log("epoch", (epoch,))
            for i, player in players.items():
                state = player.step(state.obs)
                logger.log(
                    "continue", (player.user_name, state.obs["jukugo"], state.done)
                )
                if state.done:
                    break
            epoch += 1

        # End Game
        logger.log("game_end", tuple())
        winner: JukugoRelayEnv = players[(i - 1) % num_players]
        loser: JukugoRelayEnv = player
        if epoch + i > 2:
            logger.log("win", (winner.user_name,))
            logger.log("lose", (loser.user_name,))
        else:
            logger.log("win", ("ゲームマスター",))
            logger.log("lose", ("プレイヤー",))


if __name__ == "__main__":
    run()
