# -*- coding: utf-8 -*-
import os
import re
from typing import Any, Callable, List, Optional

import yaml

src_dir, *res = os.getcwd().split("/src")

if len(res) > 0:
    import sys

    sys.path.append(src_dir + "/src")

try:
    from data.data_saver import SimpleDataSaver
except ImportError:
    raise


class AbstractStringExtractor:
    def __init__(self) -> None:
        pass

    def __call__(self, txt: str) -> bool:
        raise NotImplementedError()


class PrefixBasedSE(AbstractStringExtractor):
    def __init__(self, prefix: List[str] = []) -> None:
        self.prefix: List[str] = prefix

    def __call__(self, txt: str) -> bool:
        match: bool = False
        for pf in self.prefix:
            match |= txt.startswith(pf)
        return match


class PostfixBasedSE(AbstractStringExtractor):
    def __init__(self, postfix: List[str] = []) -> None:
        self.postfix: List[str] = postfix

    def __call__(self, txt: str) -> bool:
        match: bool = False
        for pf in self.postfix:
            match |= txt.endswith(pf)
        return match


class CountBasedSE(AbstractStringExtractor):
    def __init__(self, count: int = 2) -> None:
        self.count = count

    def __call__(self, txt: str) -> bool:
        return len(txt) == self.count


class WordsRemover(AbstractStringExtractor):
    def __init__(self, rm_words: str):
        self.rm_fn: re.Pattern = re.compile(rm_words)

    def __call__(self, txt: str):
        return self.rm_fn.search(txt) is None


class SEPipeline(AbstractStringExtractor):
    def __init__(
        self, extractors: List[AbstractStringExtractor] = [], union: bool = True
    ) -> None:
        self.extractors: List[AbstractStringExtractor] = extractors
        self.union: bool = union
        if union:
            self.fn: Callable[[bool, bool], bool] = lambda x, y: x | y
        else:
            self.fn: Callable[[bool, bool], bool] = lambda x, y: x & y

    def __call__(self, txt: str) -> bool:
        if self.union:
            match = False
        else:
            match = True
        _match: Optional[bool] = None
        for ext in self.extractors:
            _match = ext(txt)
            match = self.fn(match, _match)
        return match


class AbstractStringsProcessor:
    def __init__(
        self,
        extractor: AbstractStringExtractor,
        last: AbstractStringExtractor,
        saver: Optional[SimpleDataSaver] = None,
    ) -> None:
        self.extractor: AbstractStringExtractor = extractor
        self.last: AbstractStringExtractor = last
        self.saver: Optional[SimpleDataSaver] = saver

    def __call__(self, data: List[str]) -> Any:
        raise NotImplementedError()

    def save(self, filename: str):
        pass


class FileNameExtractor(AbstractStringsProcessor):
    def _extract(self, txt: str) -> List[str]:
        return [os.path.join(txt, f) for f in os.listdir(txt) if self.extractor(f)]

    def __call__(self, txt: str) -> List[str]:
        if self.last(txt):
            return [txt]

        files: List[str] = []
        _files: List[str] = self._extract(txt)
        for _f in _files:
            files += self(_f)
        return files


class JukugoExtractor(AbstractStringsProcessor):
    def _extract(self, data: List[str]) -> List[str]:
        return [d for d in data if self.last(d)]

    def __call__(self, txt: str) -> List[str]:
        with open(txt) as f:
            data: List[str] = yaml.safe_load(f)
        return self._extract(data)

    def save(self, data: List[str], filename: str) -> None:
        self.saver(data, filename)


def main(path: str, file_ext: FileNameExtractor, jukugo_ext: JukugoExtractor,) -> None:

    jukugo_files: List[str] = file_ext(path)
    out: List[str] = []
    for file in jukugo_files:
        out += jukugo_ext(file)
    jukugo_ext.save(out, "niji-jukugo.yml")


if __name__ == "__main__":
    file_ext: AbstractStringsProcessor = FileNameExtractor(
        extractor=SEPipeline([PrefixBasedSE(["%"]), PostfixBasedSE(["yml"])]),
        last=PostfixBasedSE(["yml"]),
    )
    jukugo_ext: AbstractStringsProcessor = JukugoExtractor(
        extractor=[],
        last=SEPipeline(
            [CountBasedSE(2), WordsRemover("[\u3041-\u309F]+")], union=False
        ),
        saver=SimpleDataSaver("../../data/", lambda x: x),
    )

    main(path="../../data/jukugo", file_ext=file_ext, jukugo_ext=jukugo_ext)
