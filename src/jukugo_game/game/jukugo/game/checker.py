from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from game.jukugo.questions.state import State
from game.jukugo.questions.variable_box import VariablesBox

_C = TypeVar("_C", bound="AbstractCheckType")


class AbstractCheckType:
    # 有効な熟語ではない場合にTrueを返すように作成してください
    comment_tmp: str
    raise_type: Exception

    def __init__(self, assert_type: str = "comment") -> None:
        self.assert_type: str = assert_type
        self.checker_name: str = self.__class__.__name__
        self.is_not_valid: bool = False
        self.comment: Optional[str] = None

    def reset(self) -> None:
        self.is_not_valid = False
        self.comment = None

    def set_comment(self, comment: str) -> None:
        if self.is_not_valid:
            self.comment = comment

    def set_valid(self, validated: bool = False) -> None:
        self.is_not_valid = validated

    def validate(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def create_comment(self, *args, **kwargs) -> str:
        raise NotImplementedError()

    def _raise(self, comment: str) -> None:
        if self.assert_type == "error":
            self.raise_type(comment)

    def get_info(self, *args) -> Tuple[Any, ...]:
        attr_list: List[Any] = []
        for attr in args:
            attr_list.append(getattr(self, attr))
        return tuple(attr_list)

    def avoid_null(self, *args, **kwargs) -> None:
        pass

    def __call__(self, *args, **kwargs) -> None:
        try:
            self.set_valid(self.validate(*args, **kwargs))
            comment: str = self.create_comment(*args, **kwargs)
            self.set_comment(comment)
            self._raise(comment)
        except self.raise_type:
            self.avoid_null()


class DefinedJukugoChecker(AbstractCheckType):
    # 定義されていない熟語を使った場合にTrueを返す
    comment_tmp: str = "{0} is not in our dictionary..."
    raise_type: Exception = KeyError

    def get_jukugo(self, **kwargs) -> str:
        _state: State = kwargs["user_state"]
        return _state.obs["jukugo"]

    def validate(self, *args, **kwargs) -> bool:
        _dict: VariablesBox = kwargs["level"]
        jukugo: str = self.get_jukugo(**kwargs)
        return not _dict.is_still_unused(jukugo)

    def create_comment(self, *args, **kwargs) -> str:
        jukugo: str = self.get_jukugo(**kwargs)
        return self.comment_tmp.format(jukugo)


class UnusedJukugoChecker(AbstractCheckType):
    # 使用済みの熟語を使った場合にTrueを返す
    comment_tmp: str = "{0} has already been used."
    raise_type: Exception = KeyError

    def get_jukugo(self, **kwargs) -> str:
        _state: State = kwargs["user_state"]
        return _state.obs["jukugo"]

    def validate(self, *args, **kwargs) -> bool:
        _dict: VariablesBox = kwargs["level"]
        jukugo: str = self.get_jukugo(**kwargs)
        return not (jukugo in _dict.unused_vars)

    def create_comment(self, *args, **kwargs) -> str:
        jukugo: str = self.get_jukugo(**kwargs)
        return self.comment_tmp.format(jukugo)


class JukugoDifferencesChecker(AbstractCheckType):
    # 熟語のリレーが規則通りでなかったときにTrueを返す
    comment_tmp: str = (
        "It has bad differences, "
        "which is not match with game rule, "
        "between the your jukugo "
        "and cpu jukugo; {0} vs {1}"
    )
    raise_type: Exception = TypeError

    def avoid_null(self, *args, **kwargs) -> None:
        comment: str = "Difference between jukugo and NoneType object cannot be found."
        self.set_comment(comment)
        self._raise(comment)

    def _get_jukugo(self, player: str = "user", **kwargs) -> str:
        if player not in ["user", "cpu"]:
            raise KeyError()
        state_key: str = "{0}_state".format(player)
        _state: State = kwargs[state_key]
        return _state.obs["jukugo"]

    def _calc_diff(
        self, user_kanji: str, cpu_kanji: str, pos_kanji: int, player_id: int
    ) -> bool:
        # posとidが一致した時に必ず漢字も一致している場合にTrueを返したい
        # posとidが一致しない場合に必ず漢字は変わっていてほしい
        pos_score: bool = pos_kanji == player_id
        kanji_score: bool = user_kanji == cpu_kanji
        diff_score: bool = pos_score == kanji_score
        return diff_score

    def _get_differences(
        self, user_jukugo: str, cpu_jukugo: str, **kwargs
    ) -> List[bool]:
        diff_list: List[bool] = []
        player_id: int = kwargs["player_id"]
        flg: bool
        for p, (u, c) in enumerate(zip(user_jukugo, cpu_jukugo)):
            flg = self._calc_diff(u, c, p, player_id)
            diff_list.append(flg)
        return diff_list

    def validate(self, *args, **kwargs) -> bool:
        user_jukugo: str = self._get_jukugo(player="user", **kwargs)
        cpu_jukugo: str = self._get_jukugo(player="cpu", **kwargs)
        diff_list: List[int] = self._get_differences(user_jukugo, cpu_jukugo, **kwargs)

        return not all(diff_list)

    def create_comment(self, *args, **kwargs) -> str:
        user_jukugo: str = self._get_jukugo(player="user", **kwargs)
        cpu_jukugo: str = self._get_jukugo(player="cpu", **kwargs)
        return self.comment_tmp.format(user_jukugo, cpu_jukugo)


class SequenceSizeChecker(AbstractCheckType):
    # 熟語数が辞書のサイズを超えてしまった場合にTrueを返す
    comment_tmp: str = (
        "A count of used jukugo must have smaller"
        "han a jukugo dictionary"
        "But the count of used jukugo is {0}, "
        "and the dictionary size is {1}"
    )
    raise_type: Exception = IndexError

    def _get_num_used_sequence(self, *args, **kwargs) -> int:
        _dict: VariablesBox = kwargs["level"]
        return len(_dict.used_ids)

    def _get_size_sequence(self, *args, **kwargs) -> int:
        _dict: VariablesBox = kwargs["level"]
        return _dict.max_ids

    def validate(self, *args, **kwargs) -> bool:
        num_used: int = self._get_num_used_sequence(*args, **kwargs)
        size_dict: int = self._get_size_sequence(*args, **kwargs)

        return num_used > size_dict

    def create_comment(self, *args, **kwargs) -> str:
        num_used: int = self._get_num_used_sequence(*args, **kwargs)
        size_dict: int = self._get_size_sequence(*args, **kwargs)
        return self.comment_tmp.format(num_used, size_dict)


class WordIDChecker(AbstractCheckType):
    # ワードに重複があった場合にTrueを返す
    comment_tmp: str = (
        "Sequence self.used_ids mustn't "
        "have two or more same ids, but; {0}. "
        "{1} is duplicated."
    )
    raise_type: Exception = KeyError

    def _get_word_list(self, *args, replace=False, **kwargs) -> List[int]:
        _dict: VariablesBox = kwargs["level"]
        id_list: List[int] = _dict.used_ids
        if replace:
            return id_list
        else:
            return list(set(id_list))

    def validate(self, *args, **kwargs) -> bool:
        raw_list: List[int] = self._get_word_list(*args, replace=True, **kwargs)
        replaced_list: List[int] = self._get_word_list(*args, replace=False, **kwargs)
        return len(raw_list) != len(replaced_list)

    def create_comment(self, *args, **kwargs) -> str:
        raw_list: list[int] = self._get_word_list(*args, replace=True, **kwargs)
        return self.comment_tmp.format(raw_list[-10:], raw_list[-1])


class CheckerPipelineBase:
    def __init__(
        self,
        checkers: List[_C],
        assert_type: str = "comment",
        valid_method: str = "union",
    ) -> None:
        self._c: List[_C] = [c(assert_type) for c in checkers]
        self.additional_props: Dict[str, Any] = {}
        self.valid_info: List[Tuple[str, bool, str]] = []
        self.valid_method: str = valid_method

    def _union(self, val: bool, checker: _C) -> bool:
        return val | checker.is_not_valid

    def _intersection(self, val: bool, checker: _C) -> bool:
        return val & checker.is_not_valid

    def get_method(self) -> Callable[[bool], bool]:
        cls_method: str = "_{0}".format(self.valid_method)
        return getattr(self, cls_method)

    @property
    def is_not_valid(self) -> bool:
        valid: bool = False
        check_method: Callable[[bool], bool] = self.get_method()
        for checker in self._c:
            valid = check_method(valid, checker)
        return valid

    @property
    def comments(self) -> List[str]:
        info: Tuple[str, bool, str]
        is_not_valid: bool
        txt: str

        error_text: List[str] = []
        for info in self.valid_info:
            is_not_valid, txt = info[1:]
            if is_not_valid:
                error_text.append(txt)

        return error_text

    def set_additional_properties(self, **kwargs) -> None:
        self.additional_props.update(**kwargs)

    @property
    def properties(self) -> Dict[str, Any]:
        props: Dict[str, Any] = self.__dict__
        props.update(**self.additional_props)
        return props

    def reset(self) -> None:
        for c in self._c:
            c.reset()
        self.valid_info = []

    def __call__(self, *args, **kwargs) -> None:
        self.reset()
        prop: Dict[str, Any] = self.properties
        for checker in self._c:
            checker(**prop)
            self.set_valid_info(checker)

    # return List of (checker_name, valid, comment)
    def set_valid_info(self, checker: _C) -> None:
        info: Tuple[str, bool, str] = checker.get_info(
            "checker_name", "is_not_valid", "comment"
        )
        self.valid_info.append(info)


class JukugoCheckerPipeline(CheckerPipelineBase):
    def __init__(
        self, level: VariablesBox, *args, player_id: int = 0, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.level: VariablesBox = level
        self.player_id: int = player_id
        self.adversary_id: int = (player_id + 1) % 2

    def __call__(self, cpu_state: State, user_state: State, *args, **kwargs) -> None:
        self.set_additional_properties(
            **{"cpu_state": cpu_state, "user_state": user_state}
        )
        super().__call__(*args, **kwargs)
