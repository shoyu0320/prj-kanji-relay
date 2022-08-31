# -*- coding: utf-8 -*-
import os

import requests


def get_html(url: str = "https://www.kanjipedia.jp/") -> str:
    """URLからソースコードを取り出し、HTMLをテキストとして抽出します。

    Args:
        url (str, optional): 保存したいHTMLデータを持つURLを指定します.
            Defaults to "https://www.kanjipedia.jp/".

    Returns:
        str: HTMLのテキストデータ
    """
    res = requests.get(url)
    raw_data: str = res.text

    return raw_data


def save_text(text: str, output: str = "data/kanjipedia.html") -> None:
    """テキストを指定したファイルに保存します。

    Args:
        text (str, optional): 保存したいテキストを指定します.
        output (str, optional): 作成したHTMLデータの保存先を指定します.
            Defaults to "data/kanjipedia.html".
    """

    data_path = "/".join(output.split("/")[:-1])
    print(f"The data is being saved in {data_path}")
    if os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)

    with open(output, "w") as f:
        f.write(text)
        print("Save is done!")


def save_html_from_url(
    url: str = "https://www.kanjipedia.jp/", output: str = "data/kanjipedia.html"
) -> None:
    """URLからソースコードを取り出し、HTMLをテキストとして保存します。

    Args:
        url (str, optional): 保存したいHTMLデータを持つURLを指定します.
            Defaults to "https://www.kanjipedia.jp/".
        output (str, optional): 作成したHTMLデータの保存先を指定します.
            Defaults to "data/kanjipedia.html".
    """
    raw_text = get_html(url=url)
    save_text(raw_text, output=output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.kanjipedia.jp/",
        help="Specifies a URL of which you would like to get html data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/kanjipedia.html",
        help="Specifies a folder to save created html data.",
    )
    args = parser.parse_args()

    print(args.url)
    save_html_from_url(url=args.url, output=args.output)
