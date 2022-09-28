from typing import Dict, List

import yaml


class JukugoList:
    level2dir: Dict[str, str] = {"normal": "../../data/niji-jukugo.yml"}

    def __init__(self):
        self.level: Dict[str, List[str]] = {}
        for k, v in self.level2dir.items():
            self.level[k] = self._get_jukugo_list(v)

    def _get_jukugo_list(self, jukugo_dir: str) -> List[str]:
        with open(jukugo_dir) as f:
            data: List[str] = yaml.safe_load(f)
        return data
