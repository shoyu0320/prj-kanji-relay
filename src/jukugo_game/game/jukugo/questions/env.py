from typing import Any, Dict, List, Optional, TypeVar, Union

import numpy as np
import yaml
from game.jukugo.game.checker import AbstractCheckType, JukugoCheckerPipeline
from game.jukugo.utils.logger import GameLogger

from .state import State
from .variable_box import VariablesBox

_C = TypeVar("_C", bound=AbstractCheckType)


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
        checkers: List[_C] = []
    ) -> None:
        super().__init__()
        self.jukugo_box: VariablesBox
        if isinstance(jukugo_list, VariablesBox):
            self.jukugo_box = jukugo_list
        else:
            self.jukugo_box = VariablesBox(jukugo_list, box_id=user_name, name=user_name)
        self.user_id: int = user_id
        self.user_name: Optional[str] = user_name
        self.checker: JukugoCheckerPipeline = JukugoCheckerPipeline(
            checkers=checkers,
            level=self.jukugo_box,
            player_id=self.user_id,
            assert_type="error",
            valid_method="union"
        )
        self.previous_state: State = State()

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
        jukugo: str
        if len(unused_jukugo) > 0:
            jukugo = np.random.choice(unused_jukugo)
        else:
            jukugo = None
        return jukugo

    def set_new_observation(self,
                            jukugo: str,
                            jukugo_id: Optional[int] = None,
                            yomi: Optional[str] = None
                            ) -> None:
        # 観測更新
        # TODO variable_boxにTuple[jukugo, jukugo_id, yomi]を与えて絞り出す
        self.state.set_obs({
            "jukugo": jukugo,
            "jukugo_id": jukugo_id,
            "yomi": yomi
        })
        if self.previous_state.obs.get("jukugo", None) is not None:
            self.checker(cpu_state=self.previous_state, user_state=self.state)

    def set_new_info(self, info: Dict[str, Any] = {}) -> None:
        unused: List[str] = self.jukugo_box.get_named_unused_vars(self.user_name)
        info.update(
            unused_jukugo=unused,
            valid_info=self.checker.valid_info
        )
        self.state.set_info(info)

    def set_new_done(self, is_done: bool = False) -> None:
        is_done |= self.checker.is_not_valid
        self.state.set_done(is_done)

    # 相手がnot validな熟語を渡してきたとき+1
    # set_new_infoの後
    def set_new_reward(self) -> None:
        if self.previous_state.done:
            self.state.reward += 1
        if self.state.done:
            self.state.reward -= 1

    def set_new_state_without_obs(self) -> None:
        self.set_new_info()
        self.set_new_done()
        self.set_new_reward()

    def set_new_state(self, new_state: State) -> None:
        self.state = new_state
        self.checker(cpu_state=self.previous_state, user_state=self.state)

    def reset(self, jukugos: Optional[Union[str, List[str]]] = None) -> Dict[str, str]:
        self.jukugo_box.reset()
        self.state.reset_std()
        self.previous_state.reset_std()
        self.checker.reset()

        # 初期状態の更新
        if isinstance(jukugos, str):
            self.jukugo_box.increase(jukugos)
        elif isinstance(jukugos, list):
            self.jukugo_box.increase_seq(jukugos)

        jukugo = self._get_new_jukugo()
        self.set_new_observation(jukugo=jukugo)
        self.set_new_state_without_obs()
        return self.state

    def _step(self) -> str:
        # 受け取った熟語を使用済に
        previous_jukugo: Optional[str] = self.previous_state.obs.get("jukugo")

        # 提出する熟語を使用済に
        current_jukugo: Optional[str] = self._get_new_jukugo(previous_jukugo)
        self.set_new_observation(jukugo=current_jukugo)

        return current_jukugo

    def step_observation(self, state: State) -> str:
        self.set_previous_state(state)
        return self._step()

    def set_previous_state(self, state: State) -> None:
        self.previous_state = state

    def step(self, state: State) -> State:
        self.jukugo_box.increase(state.obs["jukugo"])
        new_jukugo: str = self.step_observation(state)

        if new_jukugo is not None:
            self.jukugo_box.increase(new_jukugo)
        self.set_new_state_without_obs()
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
