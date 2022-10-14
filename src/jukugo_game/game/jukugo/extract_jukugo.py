import re
from typing import Dict, List, Tuple, Union

import yaml


def get_yomi(jukugo: str) -> str:
    sp: List[str] = jukugo.split("(")
    if len(sp) >= 2:
        yomi: str = sp[-1]
        yomi = yomi.replace(")", "")
        yomi = yomi.replace("/", "")
        return yomi
    else:
        return None


def get_kanji(jukugo: str) -> List[str]:
    sp: List[str] = jukugo.split("(")
    if len(sp) >= 2:
        kanji: str = sp[0]
        kanji = kanji.split("・")
        return kanji
    else:
        return None


def split_info(jukugo: str) -> Tuple[List[str], str]:
    kanji: str = get_kanji(jukugo)
    yomi: str = get_yomi(jukugo)
    return kanji, yomi


def has_two_chars(words: List[str]) -> bool:
    w: str
    flg: bool = False
    for w in words:
        flg |= len(w) == 2
    return flg


def has_only_kanji(words: List[str]) -> bool:
    p = re.compile("[ぁ-ゟ]+")
    flg: bool = True
    hiragana: str
    w: str
    for w in words:
        hiragana = p.findall(w)
        flg &= len(hiragana) > 0
    return not flg


def is_niji_jukugo(words: List[str]) -> bool:
    if words is None:
        return False
    flg: bool = True

    flg &= has_two_chars(words)
    flg &= has_only_kanji(words)

    return flg


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        type=str,
        default="../data/jukugo_list.yml",
        help=("If you save output in a DataCollector, you must set this argument."),
    )
    parser.add_argument(
        "--savedir",
        type=str,
        default="../data/niji-jukugo_list.yml",
        help=("If you save output in a DataCollector, you must set this argument."),
    )
    args = parser.parse_args()

    with open(args.inputs, "r") as f:
        kanji_inputs: Dict[str, Union[str, List[str]]] = yaml.safe_load(f)

    kanji: str
    yomi: str
    info: Dict[str, str]

    for jukugo in kanji_inputs:
        print(jukugo)
        if isinstance(jukugo, list) or (jukugo == "NG"):
            continue

        kanji, yomi = split_info(jukugo)
        if is_niji_jukugo(kanji):
            _main, *_sub = kanji
            info = {_main: {"読み": yomi}}

            with open(args.savedir, "a", encoding="utf-8") as f:
                yaml.safe_dump(info, f, encoding="utf8", allow_unicode=True)


if __name__ == "__main__":
    main()
