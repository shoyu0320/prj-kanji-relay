from typing import Dict, List, Optional, Set

import yaml


class JukugoList:
    level2dir: Dict[str, str] = {
        "kanjipedia": {"jdir": "../../data/niji-jukugo_list.yml", "jtype": "dict"},
    }

    def __init__(self, scope: Optional[List[int]] = None, mode: Optional[str] = None):
        self.level: Dict[str, List[str]] = {}
        for k, v in self.level2dir.items():
            j_list: List[str] = self._get_jukugo(**v)
            self.level[k] = self.clean_list(j_list)
        self.scope: Optional[List[int]] = scope
        self.mode: Optional[str] = mode

    def set_scope(self, scope: Optional[List[int]] = None) -> None:
        self.scope = scope

    def set_mode(self, mode: Optional[str] = None) -> None:
        self.mode = mode

    def clean_list(self, j_list: List[str]) -> List[str]:
        j: str
        new_set: Set[str] = set([])
        for j in j_list:
            if len(j) != 2:
                continue
            new_set.add(j)
        return list(new_set)

    def _get_jukugo(self, jdir: str, jtype: str = "dict") -> List[str]:
        if jtype == "dict":
            return self._get_jukugo_dict(jdir)
        elif jtype == "list":
            return self._get_jukugo_list(jdir)

    def _get_jukugo_list(self, jukugo_dir: str) -> List[str]:
        with open(jukugo_dir) as f:
            data: List[str] = yaml.safe_load(f)
        return data

    def _get_jukugo_dict(self, jukugo_dir) -> List[str]:
        with open(jukugo_dir) as f:
            data: Dict[str, Dict[str]] = yaml.safe_load(f)
            list_data: List[str] = list(data.keys())
        return list_data
