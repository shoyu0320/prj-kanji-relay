import os
from typing import Any, List, Optional, Union

# TODO runnerクラス、チェッカークラス（熟語の部分一致など）、
src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")


from game.checker import JukugoChecker
from game.level import JukugoList
from questions.env import JukugoRelayEnv
from questions.state import State
from questions.variable_box import VariablesBox
from utils.logger import GameLogger


class AbstractPlayer:
    def __init__(
        self, level: List[str], player_id: int = 0, name: Optional[str] = None,
    ) -> None:
        self.name: str = self.input_name(name)
        self.player_id: int = player_id
        self.level: VariablesBox(level) = VariablesBox(level)
        self.checker: Optional[JukugoChecker] = JukugoChecker(
            self.level, self.player_id
        )
        self.set_env(self.level)
        self.logger: GameLogger = GameLogger()

    def input_name(self, name: Optional[str] = None) -> str:
        raise NotImplementedError()

    def set_env(self, variables: VariablesBox):
        self.env: JukugoRelayEnv = JukugoRelayEnv(variables, self.player_id, self.name)
        self.env.reset()

    def submit(
        self, opponent_state: State, self_state: Optional[Union[str, State]] = None
    ) -> State:
        self.level.increase(self.env.state.obs["jukugo"])
        self.logger.log(
            "continue", (self.name, self_state.obs["jukugo"], self_state.done)
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
        self, opponent_state: State, self_state: Optional[Union[str, State]]
    ) -> State:
        self.env._set_new_state(self_state)
        self.checker(opponent_state, self.env.state)
        return super().submit(opponent_state, self.env.state)


class EnvStepPlayer(AbstractPlayer):
    def input_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError(
                "Name type must be str;" f"but input name type is {type(name)}"
            )
        return name

    def submit(
        self, opponent_state: State, self_state: Optional[Union[str, State]] = None
    ) -> State:
        self.env._step(opponent_state.obs)
        self.checker(opponent_state, self.env.state)
        return super().submit(opponent_state, self.env.state)


class InputPlayer(AbstractPlayer):
    def input_name(self, name: Optional[str] = None) -> str:
        return input()

    def submit(
        self, opponent_state: State, self_state: Optional[Union[str, State]] = None
    ) -> State:
        used: bool = True
        while used:
            self_state = input()
            used = not self.level.is_still_unused(self_state)

            # State更新
            self.env._set_new_state(self_state)
            self.checker(opponent_state, self.env.state)

        self.env._set_new_state(self_state)
        return super().submit(opponent_state, self.env.state)


class GameMaster(AbstractPlayer):
    def input_name(self, name: str):
        return "GameMaster"

    def first(self, mode: str = "input",) -> State:
        if mode == "input":
            used: bool = True
            while used:
                self_state = input()
                used = not self.level.is_still_unused(self_state)
            self.env._set_new_state(self_state)
        elif mode == "auto":
            self.env.reset()
        else:
            raise ValueError("Variable 'mode' must be chosen from [input, auto]")
        self.level.increase(self.env.state.obs["jukugo"])
        return self.env.state


def main():
    jukugo_list: JukugoList = JukugoList()
    game_master: GameMaster = GameMaster(
        jukugo_list.level["normal"], player_id=0, name="GameMaster"
    )
    cpu: AbstractPlayer = EnvStepPlayer(
        jukugo_list.level["normal"], player_id=0, name="CPU1"
    )
    # player: AbstractPlayer = InputPlayer(jukugo_list.level["normal"], player_id=1)
    player: AbstractPlayer = EnvStepPlayer(
        jukugo_list.level["normal"], player_id=1, name="CPU2"
    )
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
