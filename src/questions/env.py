import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import yaml

src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")


class Env:
    def __init__(self) -> None:
        self.obs: Dict[str, str] = {}
        self.info: Dict[str, Any] = {}
        self.reward: float = 0.0
        self.done: bool = False

    def reset(self) -> Dict[str, str]:
        pass

    def step(
        self, obs: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, Any], float, bool]:
        raise NotImplementedError()


class JukugoRelayEnv(Env):
    def __init__(
        self,
        jukugo_dict: List[str] = [],
        user_id: int = 0,
        user_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.jukugo_dict: List[str] = jukugo_dict
        self.used_jukugo: List[str] = []
        self.user_id: int = user_id
        self.user_name: Optional[str] = user_name

    @property
    def dict_size(self) -> int:
        return len(self.jukugo_dict)

    def _get_unused_jukugo(self) -> np.ndarray:
        return np.setdiff1d(self.jukugo_dict, self.used_jukugo)

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

    def is_in_unused(self, jukugo: str) -> bool:
        return jukugo in self.jukugo_dict

    def _get_new_state(self, jukugo: str) -> Tuple[Dict[str, Any], float, bool]:
        done: bool = False
        reward: float = 0
        if jukugo is None:
            done = True
            reward -= 1

        judge: bool = self.is_in_unused(jukugo)
        info: Dict[str, Any] = {"used_jukugo": self.used_jukugo, "is_in": judge}

        if not judge:
            reward -= 1
        return info, reward, done

    def reset(self, jukugos: Optional[Union[str, List[str]]] = None) -> Dict[str, str]:
        self.used_jukugo = []
        self.update_used_jukugo(jukugos)
        jukugo = self._get_new_jukugo()
        return {"jukugo": jukugo}

    def step(
        self, obs: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, Any], float, bool]:
        old_jukugo: Optional[str] = obs.get("jukugo")
        self.update_used_jukugo(obs)
        new_jukugo: str = self._get_new_jukugo(old_jukugo)

        new_obs: Dict[str, str] = {"jukugo": new_jukugo}
        self.update_used_jukugo(new_obs)

        info: Dict[str, Any]
        reward: float
        done: bool

        info, reward, done = self._get_new_state(new_jukugo)

        return new_obs, info, reward, done

    def update_used_jukugo(
        self, jukugos: Optional[Union[str, List[str]]] = None
    ) -> None:
        if isinstance(jukugos, str):
            self.used_jukugo.append(jukugos)
        elif isinstance(jukugos, dict):
            self.used_jukugo.append(jukugos["jukugo"])
        elif isinstance(jukugos, list):
            for jukugo in jukugos:
                self.update_used_jukugo(jukugo)


def run():
    with open("../../data/niji-jukugo.yml") as f:
        data: List[str] = yaml.safe_load(f)

    # Set Variables
    i: int
    player: JukugoRelayEnv
    word: Dict[str, str]
    epoch: int
    done: bool
    _: Any

    # Set Constant Values
    num_players: int = 4
    num_games: int = 20
    players: Dict[str, JukugoRelayEnv] = {}
    epoch_line: str = "=" * 50
    game_line: str = "*" * 50
    continue_temp: str = "{}: 熟語: {}, ゲーム終了判定: {}"
    win_temp: str = "勝利: {}"
    lose_temp: str = "敗北: {}"

    # Create Players
    for i in range(num_players):
        players[i] = JukugoRelayEnv(
            jukugo_dict=data, user_id=i % 2, user_name=f"プレイヤー{i}"
        )

    # Create and Run Games
    for game in range(1, num_games + 1):
        print(f"Game: {game}" + game_line)

        # Initialize Constant
        epoch = 1
        done = False

        # Reset Envs
        for i in range(num_players):
            word = players[i].reset()
        print(continue_temp.format("ゲームマスター", word["jukugo"], False))

        # Start Game
        while not done:
            print(f"Epoch: {epoch}" + epoch_line)
            for i, player in players.items():
                player.update_used_jukugo(word)
                word, _, _, done = player.step(word)
                print(continue_temp.format(player.user_name, word["jukugo"], done))
                if done:
            break
            epoch += 1

        # End Game
        print(game_line)
        winner: JukugoRelayEnv = players[(i - 1) % num_players]
        loser: JukugoRelayEnv = player
        if epoch + i > 2:
            print(win_temp.format(winner.user_name))
            print(lose_temp.format(loser.user_name))
        else:
            print(win_temp.format("ゲームマスター"))
            print(lose_temp.format("プレイヤー"))


if __name__ == "__main__":
    run()
