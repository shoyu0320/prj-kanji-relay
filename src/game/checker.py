import os
from typing import List

import numpy as np

# TODO runnerクラス、チェッカークラス（熟語の部分一致など）、
src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")


from questions.state import State
from questions.variable_box import VariablesBox


class AbstractChecker:
    def __call__(self, opponent_state: State, self_state: State) -> None:
        raise NotImplementedError()


class JukugoChecker(AbstractChecker):
    def __init__(
        self, level: VariablesBox, player_id: int = 0, assert_level: str = "print"
    ) -> None:
        self.level: VariablesBox = level
        self.player_id: int = player_id
        self.assert_level: str = assert_level
        self._done: bool = False

    def reset(self):
        self._done = False

    def game_set(self):
        self._done = True

    def _check_unused(self, self_state: State) -> bool:
        jukugo: str = self_state.obs["jukugo"]
        return self.level.is_still_unused(jukugo)

    def _check_difference(self, opponent_state: State, self_state: State) -> bool:
        o_jukugo: str = opponent_state.obs["jukugo"]
        s_jukugo: str = self_state.obs["jukugo"]

        differences: str = np.array(
            [1 if o != s else -1 for o, s in zip(o_jukugo, s_jukugo)]
        )
        print(differences, o_jukugo, s_jukugo, self.player_id)
        differences[self.player_id] *= -1
        return np.all(differences + 1)

    def __call__(self, opponent_state: State, self_state: State) -> None:
        if not self._check_unused(self_state):
            jukugo: str = self_state.obs["jukugo"]
            if self.assert_level == "error":
                raise ValueError(f"{jukugo} has already been used.")
            elif self.assert_level == "print":
                print(f"使用済みの熟語です。; {jukugo}")
            self.game_set()

        elif not self._check_difference(opponent_state, self_state):
            o_jukugo: str = opponent_state.obs["jukugo"]
            s_jukugo: str = self_state.obs["jukugo"]
            if self.assert_level == "error":
                raise ValueError(
                    "It has bad differences,"
                    "which is not match with game rule,"
                    f"between the opponent jukugo"
                    f"and your one; {o_jukugo} vs {s_jukugo}"
                )
            elif self.assert_level == "print":
                print(f"ゲーム規則に反した熟語です。;" f"\n相手の熟語: {o_jukugo}\nあなたの熟語: {s_jukugo}")
            self.game_set()

        self_state.done = self._done
