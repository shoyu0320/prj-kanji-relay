import logging
import uuid
from logging import config, getLogger
from typing import Any, Dict, Tuple, Union


class LoggerBase:
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": (
                    "%(asctime)s %(name)s:%(lineno)s"
                    "%(funcName)s [%(levelname)s]: %(message)s"
                )
            }
        },
        "handlers": {
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "fileHandler": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": "../../logs/{}.log",
            },
        },
        "loggers": {
            "__main__": {
                "level": "DEBUG",
                "handlers": ["consoleHandler", "fileHandler"],
                "propagate": False,
            },
            "same_hierarchy": {
                "level": "DEBUG",
                "handlers": ["consoleHandler", "fileHandler"],
                "propagate": False,
            },
            "lower.sub": {
                "level": "DEBUG",
                "handlers": ["consoleHandler", "fileHandler"],
                "propagate": False,
            },
        },
        "root": {"level": "DEBUG", "handlers": ["fileHandler"], "propagate": False},
    }

    def __init__(self):
        log_id: str = str(uuid.uuid4())
        base: str = self.config["handlers"]["fileHandler"]["filename"]
        self.config["handlers"]["fileHandler"]["filename"] = base.format(log_id)

        config.dictConfig(self.config)
        self.logger = getLogger(__name__)


class GameLogger(LoggerBase):
    tmp: Dict[str, str] = {
        "epoch": "Epoch: {} " + "=" * 25,
        "game": "Game: {} " + "*" * 25,
        "game_end": "*" * 25,
        "continue": "{}: 熟語: {}, ゲーム終了判定: {}",
        "win": "勝利: {}",
        "lose": "敗北: {}",
    }

    def log(self, tmp: str, msg: Tuple[Union[str, int]], *args, **kwargs) -> None:
        if tmp not in self.tmp.keys():
            raise KeyError()

        txt: str = self.tmp[tmp].format(*msg)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger._log(logging.DEBUG, txt, args, **kwargs)
