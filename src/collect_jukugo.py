# -*- coding: utf-8 -*-
import copy
import os
from typing import Dict, List, Optional, Union

import yaml

src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")

try:
    from data.data_collector import AbstractDataCollector, SimpleDataCollector
    from data.data_saver import SimpleDataSaver
    from data.extract_data import identity_fn, sieve_fn
except ImportError:
    raise


def collect_data(inputs: Dict[str, str], saver: SimpleDataSaver, filename: str) -> None:
    """
    It takes a dictionary of inputs, a data saver, and a filename, and then it
    creates a data collector, resets it, digs recursively, and saves the data

    Args:
        inputs (Dict[str, str]): A dictionary of parameters.
        saver (SimpleDataSaver): SimpleDataSaver
        filename (str): The name of the file to save the data to.
    """
    data_collector: AbstractDataCollector = SimpleDataCollector(
        start_url=inputs["url"],
        output_style=inputs["style"],
        rf_words=inputs["rf_words"],
        saver=saver,
    )

    data_collector.reset()
    data_collector.dig_recursively(inputs["selectors"])
    data_collector.save(filename=filename)


def get_page_info(kana_url: str) -> List[str]:
    split_kana: List[str] = kana_url.split("/")
    base_url: str = "/".join(split_kana[:-2])
    return base_url, split_kana[-2:]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        type=str,
        default="../data/test/",
        help=("If you save output in a DataCollector, you must set this argument."),
    )
    parser.add_argument(
        "--savedir",
        type=str,
        default="../data/test/",
        help=("If you save output in a DataCollector, you must set this argument."),
    )
    args = parser.parse_args()

    kanji_file: str = f"{args.inputs}/selectors/jukugo_url.yml"
    with open(kanji_file, "r") as f:
        kanji_inputs: Dict[str, Union[str, List[str]]] = yaml.safe_load(f)

    saver: SimpleDataSaver = SimpleDataSaver(savedir=args.savedir, fn=sieve_fn)
    collect_data(kanji_inputs, saver, filename="hiragana.yml")

    jukugo_file: str = f"{args.inputs}/selectors/kanji_url.yml"
    with open(jukugo_file, "r") as f:
        jukugo_inputs: List[str] = yaml.safe_load(f)

    hiragana_file: str = f"{args.inputs}/urls/hiragana.yml"
    with open(hiragana_file, "r") as f:
        hiragana: List[str] = yaml.safe_load(f)

    kana_inputs: Dict[str, Union[str, List[str]]] = copy.deepcopy(jukugo_inputs)
    url_base: Optional[str] = None
    kana_dir: Optional[str] = None
    num_pages: Optional[str] = None
    saver.change_converter(fn=identity_fn)

    for kana in hiragana:
        url_base, [kana_dir, num_pages] = get_page_info(kana)

        for page in range(1, int(num_pages) + 1):
            kana_url: str = os.path.join(url_base, kana_dir, str(page))
            kana_inputs.update(url=kana_url)
            save_file: str = os.path.join(kana_dir, str(page)) + ".yml"
            collect_data(kana_inputs, saver, filename=save_file)


if __name__ == "__main__":
    main()
