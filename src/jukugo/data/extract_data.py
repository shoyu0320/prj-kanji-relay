# -*- coding: utf-8 -*-
from typing import Any, List


def _has_num_at_last(data: str):
    """
    It takes a string, splits it on the forward slash, and checks if the last
    element is a number

    Args:
        data (str): The data to be processed.

    Returns:
        The last part of the string is being returned.
    """
    return data.split("/")[-1].isdigit()


def identity_fn(output: Any) -> Any:
    """
    "Return the input."

    The function takes an argument `output` of type `Any` and returns a value of
    type `Any`

    Args:
        output (Any): The output of the previous layer.

    Returns:
        The output is being returned.
    """
    return output


def sieve_fn(output: List[str]) -> List[str]:
    """
    > It returns `True` if the last part of the string is a number, and `False`
    otherwise

    Args:
        output (List[str]): List[str] -> The output of the previous function.
    """
    _out: List[str] = []

    for out in output:
        if _has_num_at_last(out):
            _out.append(out)

    return _out
