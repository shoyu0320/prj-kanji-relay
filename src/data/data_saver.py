# -*- coding: utf-8 -*-
import os
from typing import Any, Callable, List, Optional

import yaml


class SimpleDataSaver:
    def __init__(self, savedir: str, fn: Callable[..., Any]):
        """
        It takes a function and a directory, and returns a function that saves
        the output of the original function to the directory

        Args:
            savedir (str): The directory to save the file to.
            fn (Callable[..., Any]): The function to be wrapped.
        """
        self.savedir: str = savedir
        self.fn: Callable[..., Any] = fn

    def _check_dir(self, filename: str) -> None:
        """
        If the directory of the file doesn't exist, create it

        Args:
            filename (str): The name of the file to save the model to.
        """
        save_dir: str = os.path.dirname(filename)

        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

    def get_filename(self, filename: str):
        """
        > This function checks if the directory exists, if not, it creates it

        Args:
            filename (str): the name of the file to be saved

        Returns:
            The filename is being returned.
        """
        _filename: str = os.path.join(self.savedir, filename)
        self._check_dir(filename=_filename)
        return _filename

    def __call__(self, output: Any, filename: Optional[str] = None) -> None:
        """
        > This function takes in an output and a filename, and then writes the
        output to the filename

        Args:
            output (Any): The output of the function.
            filename (Optional[str]): The filename to write to.

        Returns:
            The output of the function is being returned.
        """
        if filename is None:
            return

        _filename: str = self.get_filename(filename)
        _output: Any = self.fn(output)

        with open(_filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(_output, f, allow_unicode=True)

    def change_converter(self, fn: Callable[..., Any]) -> None:
        """
        `change_converter` takes a function as an argument and assigns it to the
        `fn` attribute of the `Converter` instance

        Args:
            fn (Callable[..., Any]): The function to be called when the button is pressed.
        """
        self.fn = fn


def sieve_fn(output: List[str]) -> List[str]:
    """
    > It returns `True` if the last part of the string is a number, and `False`
    otherwise

    Args:
        output (List[str]): List[str] -> The output of the previous function.
    """

    def _is_valid_data(data: str):
        """
        > It returns `True` if the last part of the string is a number, and
        `False` otherwise

        Args:
            data (str): The data to be validated.

        Returns:
            a boolean value.
        """
        return data.split("/")[-1].isdigit()

    _out: List[str] = []

    for out in output:
        if _is_valid_data(out):
            _out.append(out)

    return _out
