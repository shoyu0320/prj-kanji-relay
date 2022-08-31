# -*- coding: utf-8 -*-
import os
import re
import time
from typing import Callable, Dict, List, Optional, Tuple, Union

import yaml
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")

try:
    from data.data_saver import SimpleDataSaver, sieve_fn
    from data.save_html_from_url import get_html
except ImportError:
    raise


# TODO: 記事にまとめてね！gitとにコミットもしてね！
class AbstractDataCollector:
    def __init__(
        self,
        start_url: str,
        output_style: str = "url",
        saver: Optional[SimpleDataSaver] = None,
    ) -> None:
        """
        `__init__` is a special function that is called when an object is created.

        Args:
            start_url (str): The URL to start crawling from.
            output_style (str): This is the format in which the output will be
                displayed. It can be either "url" or "domain". Defaults to url
            saver (Optional[SimpleDataSaver]): This is the object that will save
            the data.
        """
        self.init_url: str = start_url
        self.current_url: str = start_url
        self.urls: List[str] = [self.init_url]
        self.output_style: str = output_style
        self.depth: Optional[int] = None
        self.outputs: List[str] = []
        self.saver: SimpleDataSaver = saver

    def reset(self, init_depth: int = 0) -> None:
        """
        `reset` resets the crawler to its initial state

        Args:
            init_depth (int): The depth of the initial URL. Defaults to 0
        """
        self.current_url = self.init_url
        self.urls = [self.init_url]
        self.depth = init_depth

    def save(self, filename: str) -> None:
        self.saver(self.outputs, filename=filename)


# It takes a URL and a list of selectors, and returns a list of URLs
class SimpleDataCollector(AbstractDataCollector):
    def __init__(
        self,
        *args: Tuple[str],
        rf_words: List[str] = ["▲", "△", "〈", "〉"],
        sleep_time: int = 1,
        **kwargs: Dict[str, str],
    ) -> None:
        """
        `__init__` is a function that takes in a list of strings, a list of
        strings, an integer, and a dictionary of strings, and returns nothing.

        Args:
            rf_words (List[str]): A list of words that indicate the next page.
            sleep_time (int): The time to wait between each page. Defaults to 1
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.rf_regex: str = "?".join(rf_words) + "?"
        self.rf_fn: Callable[[str, str, str], str] = re.sub
        self.exist_next: bool = False
        self.sleep_time: int = sleep_time

    @property
    def _depth(self) -> int:
        """
        > If the depth is not an integer, raise a ValueError

        Returns:
            The depth of the tree.
        """
        if self.depth is None:
            raise ValueError(
                f"self.depth; {self.depth} must be integer type."
                + "Use reset method before digs."
            )
        return self.depth

    def _get_next_url(self, element: Tag) -> str:
        """
        It takes a BeautifulSoup element and returns the next url to scrape

        Args:
            element (Tag): Tag

        Returns:
            The next url is being returned.
        """
        address: str = element.get("href")
        next_url: str = self.init_url + address
        return next_url

    def reset(self, *args, **kwargs) -> None:
        """
        It resets the iterator
        """
        super().reset(*args, **kwargs)
        self.exist_next = False

    def _get_words(self, element: Tag) -> str:
        """
        > The function `_get_words` takes a `Tag` object and returns a string

        Args:
            element (Tag): Tag

        Returns:
            The text of the element.
        """
        return self.rf_fn(self.rf_regex, "", element.text)

    def _get_output(self, element: Tag) -> str:
        """
        > The function `_get_output` returns the next url or the words in the
        current page, depending on the value of `self.output_style`

        Args:
            element (Tag): The element that we're currently looking at.

        Returns:
            The output is being returned.
        """
        output: str = ""
        if (self.output_style == "url") or (self.exist_next):
            output += self._get_next_url(element)
        elif self.output_style == "word":
            output += self._get_words(element)
        return output

    def _process_html(self, data: BeautifulSoup, selector: str) -> ResultSet[Tag]:
        """
        "Return the result of calling the `select` method on the `data`
        parameter, passing in the `selector` parameter."

        The `data` parameter is a `BeautifulSoup` object, and the `selector`
        parameter is a string. The `select` method returns a `ResultSet` object,
        which is a list of `Tag` objects

        Args:
            data (BeautifulSoup): BeautifulSoup
            selector (str): The CSS selector to use to find the elements.

        Returns:
            A ResultSet object.
        """
        return data.select(selector)

    def _judge_next(self, selector: str) -> None:
        """
        If the selector ends with `a[href]`, then the next page exists

        Args:
            selector (str): The selector of the element you want to get.
        """
        self.exist_next = selector.endswith("a[href]")

    def _extract_elements(self, selector: str) -> ResultSet[Tag]:
        """
        > It takes a selector, gets the HTML from the current URL, creates a
        BeautifulSoup object, sleeps for a bit, and then returns the result of
        the `_process_html` function

        Args:
            selector (str): The CSS selector to use to extract the elements.

        Returns:
            A list of tags
        """
        text: str = get_html(self.current_url)
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")

        # whenever after accessing a URL, need to be sleep for at least 1
        # minute.
        time.sleep(self.sleep_time)
        return self._process_html(soup, selector)

    def _update_urls(self) -> None:
        """
        It updates the current url to the last url in the list of urls
        """
        if self.exist_next:
            self.current_url = self.urls[-1]

    def _push_output(self, element: Tag, selector: str) -> None:
        """
        It takes a selector and an element, and then it pushes the output of the
        selector to the output list.

        Args:
            element (Tag): The element that we're currently looking at.
            selector (str): The CSS selector for the element you want to extract.
        """
        self._judge_next(selector)
        output: str = self._get_output(element)
        self.outputs.append(output)
        self.urls.append(output)
        self._update_urls()
        print(output)

    def _push_outputs(self, elements: ResultSet[Tag], selector: str) -> None:
        """
        It takes a list of elements and a selector, and for each element, it
        pushes the element's text to the output

        Args:
            elements (ResultSet[Tag]): The elements to push to the output.
            selector (str): The CSS selector that was used to find the element.
        """
        for element in elements:
            self._push_output(element, selector)

    def get_selector(self, selectors: List[str]) -> str:
        """
        It returns the selector at the current depth

        Args:
            selectors (List[str]): A list of selectors that are used to select the
            elements.

        Returns:
            The selector at the current depth.
        """
        depth: int = self._depth
        return selectors[depth - 1]

    def dig(self, selector: str) -> None:
        """
        It takes a selector, extracts the elements, and pushes the elements to
        the output stack

        Args:
            selector (str): The CSS selector to use to extract the elements.
        """
        elements: ResultSet[Tag] = self._extract_elements(selector)
        self._push_outputs(elements, selector)

    def _increase_depth(self) -> None:
        """
        "Increase the depth by one."

        The first line of the function is a docstring. It's a string that
        describes what the function does. It's a good idea to include a
        docstring for every function you write
        """
        depth: int = self._depth
        self.depth = depth + 1

    def _decrease_depth(self) -> None:
        """
        "Decrease the depth by one."

        The first line of the function is a docstring. It's a string that
        describes what the function does. It's a good idea to include a
        docstring for every function you write
        """
        depth: int = self._depth
        self.depth = depth - 1

    def is_bottom(self, selectors: List[str]) -> bool:
        """
        It returns `True` if the depth of the current node is equal to the
        number of selectors in the list

        Args:
            selectors (List[str]): A list of strings that represent the selectors
            that are currently being
        used.

        Returns:
            The depth of the current node.
        """
        return self.depth == len(selectors)

    def dig_recursively(self, selectors: List[str]) -> None:
        """
        It takes a list of selectors, gets the current selector, extracts the
        elements pushes the output, and then recursively calls itself if it's
        not at the bottom of the tree

        Args:
            selectors (List[str]): List[str]
        """
        self._increase_depth()
        selector: str = self.get_selector(selectors)
        elements: ResultSet[Tag] = self._extract_elements(selector)

        for element in elements:
            self._push_output(element, selector)

            if not self.is_bottom(selectors):
                self.dig_recursively(selectors)

        self._decrease_depth()
        self.urls = self.urls[: self.depth]

    def dig_multiply(self, selectors: List[str]) -> None:
        """
        It digs the specified selectors

        Args:
            selectors (List[str]): A list of selectors to dig through.
        """
        for selector in selectors:
            self.dig(selector)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--selector_file",
        type=str,
        default="../data/selectors/kanji_url.yml",
        help=(
            "Set a file name including selector information for which reach to"
            "an objective data in urls."
        ),
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help=("When you set --save, DataCollector save outputs to specified file."),
    )
    parser.add_argument(
        "--savedir",
        type=str,
        default=None,
        help=("If you save output in a DataCollector, you must set this argument."),
    )
    args = parser.parse_args()

    if (args.save) and (args.savedir is None):
        raise TypeError(
            "When you set --save argument,"
            "you must set a file name for a saving output of"
            "the DataCollector by setting --savedir argument."
        )

    with open(args.selector_file, "r") as f:
        inputs: Dict[str, Union[str, List[str]]] = yaml.safe_load(f)

    saver: SimpleDataSaver = SimpleDataSaver(savedir=args.savedir, fn=sieve_fn)

    data_collector: AbstractDataCollector = SimpleDataCollector(
        start_url=inputs["url"],
        output_style=inputs["style"],
        rf_words=inputs["rf_words"],
        saver=saver,
    )

    data_collector.reset()
    data_collector.dig_recursively(inputs["selectors"])
    data_collector.save(filename="xxx.yml")


if __name__ == "__main__":
    main()
