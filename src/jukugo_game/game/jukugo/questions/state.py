from typing import Any, Dict


class State:
    def __init__(self):
        self.obs: Dict[str, Any] = {}
        self.info: Dict[str, Any] = {}
        self.reward: float = 0.0
        self.done: bool = False

    def set_obs(self, obs: Dict[str, Any]) -> None:
        self.obs = obs

    def set_info(self, info: Dict[str, Any]) -> None:
        self.info = info

    def set_done(self, done: bool) -> None:
        self.done = done

    def set_reward(self, reward: float) -> None:
        self.reward = reward

    def reset_std(self):
        self.set_obs({})
        self.set_info({})
        self.set_reward(0.0)
        self.set_done(False)
