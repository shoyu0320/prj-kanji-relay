# -*- coding: utf-8 -*-
import os
import time
from typing import List, Optional

import requests
import yaml
from bs4 import BeautifulSoup
from bs4.element import Tag

src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")


def is_jukugo(word: str, need: List[str], waste: List[str]) -> bool:
    n: str
    w: str
    judge: List[bool] = []
    for n in need:
        judge.append(n in word)
    for w in waste:
        judge.append(w not in word)
    return all(judge)


def get_kanji(soup: BeautifulSoup) -> str:
    tag: Tag = soup.select("meta[name=keywords]")
    text: str = tag[0].get("content")
    kanji: str = text.split(",")[0]
    if len(kanji) > 1:
        # 漢字は一文字なのでそれより大きい場合はNG
        return None
    return kanji


def get_subkanji(soup: BeautifulSoup) -> str:
    tag: Tag = soup.select("p[class=subKanji]")
    if len(tag) == 0:
        return None
    subkanji: str = tag[0].get_text()
    return subkanji


def get_jukugo(
    word: str, kanji: Optional[str], subkanji: Optional[str], symbol: str = "@?@",
) -> str:
    jukugo: str = ""
    if kanji is not None:
        jukugo += word.replace(symbol, kanji) + "/"
    if subkanji is not None:
        jukugo += word.replace(symbol, subkanji)
    jukugo = clean_jukugo(jukugo, ["$", "〈", "〉"])
    return jukugo


def clean_jukugo(jukugo: str, removal: List[str]) -> str:
    rm: str
    for rm in removal:
        jukugo = jukugo.replace(rm, "")
    return jukugo


def get_modified_word(tag: Tag, buffer: str = "$", space: str = "%") -> List[str]:
    tag.insert(0, "・")
    tag.append("・")

    text: str = tag.get_text()
    text = text.replace("・", f"{buffer}・{buffer}")
    text = text.replace(" ", space)
    return text.split("・")


def change_img_to_sym(soup: BeautifulSoup, symbol: str = "@?@") -> BeautifulSoup:
    tag: Tag
    img_list: List[Tag] = soup.select("p[id=kanjiOyaji] > img")
    if len(img_list) == 0:
        return soup

    img_html: str = img_list[0].get("src")
    modified_img: str = img_html.replace("180", "16")

    for tag in soup.find_all("img"):
        if tag.get("src") == modified_img:
            tag.replace_with(symbol)
    return soup


def collect_jukugo(soup: BeautifulSoup, selector: str, symbol: str) -> List[str]:
    tag: List[Tag] = soup.select(selector)
    kanji: Optional[str] = get_kanji(soup)
    subkanji: Optional[str] = get_subkanji(soup)

    if kanji is not None:
        symbol = kanji

    if "href" in selector:
        return collect_jukugo_top(tag, kanji, subkanji, symbol)
    else:
        return collect_jukugo_bottom(tag, kanji, subkanji, symbol)


def collect_jukugo_top(
    tag: List[Tag], kanji: Optional[str], subkanji: Optional[str], symbol: str
) -> List[str]:
    t: Tag
    word: str
    jukugo: str
    jukugo_list: List[str] = []
    for t in tag:
        word = t.get_text()
        if len(word) > 1:
            jukugo = get_jukugo(word, kanji, subkanji, symbol)
            jukugo_list += [jukugo]
    return jukugo_list


def collect_jukugo_bottom(
    tag: List[Tag], kanji: Optional[str], subkanji: Optional[str], symbol: str
) -> List[str]:
    t: Tag
    w: str
    jukugo_list: List[str] = []
    for t in tag:
        word = get_modified_word(t, "$", "%")
        for w in word:
            if is_jukugo(w, [")$", "("], ["%"]):
                jukugo_list += [get_jukugo(w, kanji, subkanji, symbol)]
    return jukugo_list


def main():
    parser: str = "html.parser"
    url: str
    tag: Tag
    kanji_address: List[str] = []
    jukugo_list: List[str] = []
    flg_break: bool = False
    first: Optional[str] = None
    max_bushu: int = 30
    max_pages: int = 100
    first_tmp: str = "\r部首画数: {0}/{1}, 頁数: {2}/{3}"
    second_tmp: str = "\rURL数: {0}/{1}"
    save_dir: str = "../../data/jukugo_list.yml"
    symbol: str = "@?@"

    for d0 in ["https://www.kanjipedia.jp/"]:
        for d1 in ["sakuin"]:
            for d2 in ["bushu"]:
                for d3 in range(1, max_bushu):
                    for d4 in range(1, max_pages):
                        print(first_tmp.format(d3, max_bushu, d4, max_pages), end="")
                        url = os.path.join(d0, d1, d2, str(d3), str(d4))
                        res = requests.get(url)
                        bs = BeautifulSoup(res.text, parser)
                        flg_break = first == bs.get_text()
                        if first is None:
                            first = bs.get_text()
                        if flg_break:
                            break
                        tag = bs.select("dd > ul > li > a[href]")
                        tag = [t.get("href").split("/") for t in tag]
                        kanji_address += [os.path.join(d0, *t) for t in tag]
                        time.sleep(0.1)
                    flg_break = False
                    first = None

        for d1 in ["kanji"]:
            size: int = len(kanji_address)
            for n, d2 in enumerate(kanji_address):
                if "other" in d2:
                    continue
                jukugo_list = []
                res = requests.get(d2)
                bs = BeautifulSoup(res.text, parser)
                bs = change_img_to_sym(bs, symbol)
                for d3 in bs.findAll(["sup"]):
                    d3.decompose()
                for d3 in ["li > div > p", "li > a[href]"]:
                    jukugo_list += collect_jukugo(bs, d3, symbol)
                print(second_tmp.format(n, size), end="")
                time.sleep(0.1)

                with open(save_dir, "a", encoding="utf-8") as f:
                    yaml.safe_dump(jukugo_list, f, encoding="utf8", allow_unicode=True)


if __name__ == "__main__":
    main()
