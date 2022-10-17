from typing import Any, Dict, List, Optional, TypeVar, Union

import numpy as np
from game.jukugo.questions.env import JukugoRelayEnv
from game.jukugo.questions.state import State
from game.jukugo.questions.variable_box import VariablesBox
from game.jukugo.utils.logger import GameLogger

from .checker import (DefinedJukugoChecker, JukugoDifferencesChecker,
                      SequenceSizeChecker, UnusedJukugoChecker, WordIDChecker)
from .level import JukugoList

_C = TypeVar("_C", bound="LevelChangeableESPlayer")


class AbstractPlayer:
    def __init__(
        self, level: List[str], player_id: int = 0, name: Optional[str] = None,
    ) -> None:
        self.name: str = self.input_name(name)
        self.player_id: int = player_id
        self.level: VariablesBox(level) = VariablesBox(level)
        checkers: List[_C] = [
                DefinedJukugoChecker,
                UnusedJukugoChecker,
                JukugoDifferencesChecker,
                SequenceSizeChecker,
                WordIDChecker
            ]
        self.set_env(self.level, checkers)
        self.logger: GameLogger = GameLogger()

    def set_id(self, player_id: int = 0) -> None:
        self.player_id = player_id

    def reset(self, jukugo: Optional[str] = None) -> None:
        self.env.reset(jukugo)

    def input_name(self, name: Optional[str] = None) -> str:
        raise NotImplementedError()

    def set_env(self, variables: VariablesBox, checkers: List[_C] = []) -> None:
        self.env: JukugoRelayEnv = JukugoRelayEnv(
            variables,
            self.player_id,
            self.name,
            checkers
        )
        self.env.reset()

    def submit(
        self, cpu_state: State, user_state: Optional[Union[str, State]] = None
    ) -> State:
        self.level.increase(self.env.state.obs["jukugo"])
        self.logger.log(
            "continue", (self.name, user_state.obs["jukugo"], user_state.done)
        )
        return self.env.state


class DummyPlayer(AbstractPlayer):
    def input_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError(
                "Name type must be str; but input name type is {type(name)}"
            )
        return name

    def submit(
        self, cpu_state: State, user_state: Optional[Union[str, State]]
    ) -> State:
        self.env.set_new_state(user_state)
        state: State = super().submit(cpu_state, self.env.state)
        self.env.set_new_state_without_obs()
        return state


class EnvStepPlayer(AbstractPlayer):
    def input_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError(
                "Name type must be str;" f"but input name type is {type(name)}"
            )
        return name

    def submit(
        self, cpu_state: State, user_state: Optional[Union[str, State]] = None
    ) -> State:
        return self.step(cpu_state)


class LevelChangeableESPlayer(EnvStepPlayer):
    difficulties: Dict[str, float] = {
        "master": 1.0,
        "hard": 0.3,
        "normal": 0.1,
        "easy": 0.05,
    }

    def __init__(self, *args, difficulty: str = "normal", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.level_rate: float = self.difficulties[difficulty]
        available_jukugo: List[int] = self._create_user_dict()
        self.level.set_available_list(available_jukugo)

    def _create_user_dict(self) -> List[int]:
        available_ids: List[int] = list(self.level.full_set)
        size: int = int(self.level.max_ids * self.level_rate)
        samples: List[int] = np.random.choice(
            available_ids, replace=False, size=size
        ).tolist()
        return samples

    @classmethod
    def create_all_computers(
        cls,
        jukugo_list: List[str],
        player_id: int = 0,
        name: str = "computer"
    ) -> Dict[str, _C]:
        return {
            d: cls(
                jukugo_list,
                player_id=player_id,
                name=name,
                difficulty=d
            ) for d in cls.difficulties.keys()
        }


class InputPlayer(AbstractPlayer):
    def input_name(self, name: Optional[str] = None) -> str:
        return input()

    def submit(
        self, cpu_state: State, user_state: Optional[Union[str, State]] = None
    ) -> State:
        while not self.env.checker.is_not_valid:
            # Stateセットするだけ
            user_state = input()
            self.env.set_new_state(user_state)

        self.env.set_new_state(user_state)
        state: State = super().submit(cpu_state, self.env.state)
        self.env.set_new_state_without_obs()
        return state


class GameMaster(AbstractPlayer):
    def input_name(self, name: str):
        return "GameMaster"

    def first(self, mode: str = "input",) -> State:
        state: State
        if mode == "input":
            while not self.checker.is_not_valid:
                state = input()
                self.env.set_new_state(state)
            self.env.set_new_state_without_obs()
        elif mode == "auto":
            self.env.reset()
        else:
            raise ValueError("Variable 'mode' must be chosen from [input, auto]")
        self.level.increase(self.env.state.obs["jukugo"])
        return self.env.state


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--play",
        action="store_true",
        help=("If you play the game, you must set this command."),
    )
    args = parser.parse_args()

    jukugo_list: JukugoList = JukugoList()
    game_master: GameMaster = GameMaster(
        jukugo_list.level["kanjipedia"], player_id=0, name="GameMaster"
    )
    cpu: AbstractPlayer = LevelChangeableESPlayer(
        jukugo_list.level["kanjipedia"], player_id=0, level="hard", name="HardCPU"
    )
    cpu.reset()
    if args.play:
        player: AbstractPlayer = InputPlayer(
            jukugo_list.level["kanjipedia"], player_id=1
        )
    else:
        player: AbstractPlayer = LevelChangeableESPlayer(
            jukugo_list.level["kanjipedia"], player_id=1, level="easy", name="EasyCPU"
        )
    player.reset()
    print(f"{cpu.name} vs {player.name}")

    # logger
    logger: GameLogger = GameLogger()
    epoch: int = 1
    _: Any

    state: str = game_master.first(mode="auto")
    logger.log("continue", (game_master.name, state.obs["jukugo"], False))

    # Start Game
    while not state.done:
        logger.log("epoch", (epoch,))
        for i, p in enumerate([cpu, player]):
            state = p.submit(state, None)
            if state.done:
                break
        epoch += 1

    # End Game
    logger.log("game_end", tuple())
    winner: JukugoRelayEnv = [cpu, player][(i - 1) % 2]
    loser: JukugoRelayEnv = p
    if epoch + i > 2:
        logger.log("win", (winner.name,))
        logger.log("lose", (loser.name,))
    else:
        logger.log("win", (game_master.name,))
        logger.log("lose", (" & ".join([p.name for p in [cpu, player]]),))


if __name__ == "__main__":
    main()
