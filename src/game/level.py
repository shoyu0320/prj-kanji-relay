from typing import Dict, List, Set

import yaml


class JukugoList:
    level2dir: Dict[str, str] = {"normal": "../../data/niji-jukugo_list.yml"}
    # level2dir: Dict[str, str] = {"normal": "../../data/niji-jukugo.yml"}

    def __init__(self):
        self.level: Dict[str, List[str]] = {}
        for k, v in self.level2dir.items():
            j_list: List[str] = list(self._get_jukugo_list(v).keys())
            self.level[k] = self.clean_list(j_list)

    def clean_list(self, j_list: List[str]) -> List[str]:
        j: str
        new_set: Set[str] = set([])
        for j in j_list:
            if len(j) != 2:
                continue
            new_set.add(j)
        return list(new_set)

    def _get_jukugo_list(self, jukugo_dir: str) -> List[str]:
        with open(jukugo_dir) as f:
            data: List[str] = yaml.safe_load(f)
        return data
