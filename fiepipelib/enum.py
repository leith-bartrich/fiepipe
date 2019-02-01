import typing
from enum import Enum

T = typing.TypeVar("T", bound=Enum)


def get_worse_enum(first: T, second: T) -> T:
    """Assumes higher values are 'worse' than lower values"""
    if first.value > second.value:
        return first
    else:
        return second
