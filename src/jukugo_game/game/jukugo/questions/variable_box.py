import random
from typing import Dict, FrozenSet, List, Optional, TypeVar, Union

_L = TypeVar("_L", bound=Union[int, str])


class VariablesBox:
    def __init__(
        self,
        variables: List[_L],
        box_id: _L = 0,
        players: List[str] = [],
    ) -> None:
        self.variables: List[_L] = variables
        self.box_id: _L = box_id
        self.used_ids: List[int] = []
        self.max_ids: int = len(variables)
        self.players: Dict[str, List[int]] = {}

    def __setitem__(self, key: str, val: List[int]) -> None:
        self.players[key] = val

    def __getitem__(self, key: str) -> List[int]:
        if key not in self.players:
            return self.full_set
        return set(self.players[key])

    def get_named_unused_set(self, key: str) -> List[int]:
        used_ids: FrozenSet[int] = set(self.used_ids)
        return list(self[key] - used_ids)

    def get_named_unused_vars(self, key: str) -> List[str]:
        output: List[_L] = []
        us: int
        available_set: List[str] = self.get_named_unused_set(key)
        for us in available_set:
            output += [self.variables[us]]
        return output

    # TODO プレイヤーごとのフルセットを作成する
    def reset(self):
        self.used_ids = []

    @property
    def full_set(self) -> FrozenSet[int]:
        return set(range(self.max_ids))

    @property
    def unused_set(self) -> List[int]:
        used_ids: FrozenSet[int] = set(self.used_ids)
        return list(self.full_set - used_ids)

    @property
    def unused_vars(self) -> List[_L]:
        output: List[_L] = []
        us: int
        for us in self.unused_set:
            output += [self.variables[us]]
        return output

    def _check_id_list(self) -> None:
        # unused list のサイズのみで簡易チェックする
        if len(self.used_ids) > self.max_ids:
            raise IndexError(
                "Sequence size of self.used_ids has larger size"
                f"than {self.max_ids}; number of variables"
            )
        if len(self.used_ids) != len(set(self.used_ids)):
            raise ValueError(
                "Sequence self.used_ids mustn't"
                f"have two or more same ids, but; {self.used_ids}"
            )

    def is_still_unused(self, val: _L) -> bool:
        if val in self.unused_vars:
            return True
        else:
            print(f"辞書にない熟語です。; {val}")
            return False

    def set_available_list(self, available_samples: List[int]) -> None:
        unavailable_samples: FrozenSet[int] = self.full_set - set(available_samples)
        self.add(list(unavailable_samples))

    def add(self, used_ids: List[int]) -> None:
        for u_ids in used_ids:
            self.add2used(u_ids)
            self._check_id_list()

    def add2used(self, used_id: int) -> None:
        self.used_ids.append(used_id)
        self._check_id_list()

    def push(self, val: _L) -> None:
        self.variables += [val]
        self.max_ids += 1

    def push_seq(self, vals: List[_L]) -> None:
        self.variables += vals
        self.max_ids += len(vals)

    def pull(self) -> List[_L]:
        sample: int = random.choice(self.unused_set)
        self.add2used(sample)
        return [self.variables[sample]]

    def pull_seq(self, n_samples: int = 1) -> List[_L]:
        output: List[_L] = []
        for _ in range(n_samples):
            output += self.pull()
        return output

    def increase(self, val: Optional[_L]) -> None:
        if val in self.variables:
            _id: int = self.variables.index(val)
            self.add2used(_id)

    def increase_seq(self, vals: List[_L]) -> None:
        v: List[_L]
        for v in vals:
            self.increase(v)
