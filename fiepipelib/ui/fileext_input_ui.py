import typing
import pathlib
import abc

from fieui.InputModalUI import AbstractInputModalUI, T
from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI

def validate(v: str) -> typing.Tuple[bool,str]:
    if not v.startswith('.'):
        return False, v
    if v == '.':
        return False, v
    if v == "":
        return False, v

    return True, v


class AbstractFileExtInputUI(AbstractInputModalUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        return validate(v)


class AbstractFileExtDefaultInputUI(AbstractInputDefaultModalUI[str]):

    def validate(self, v: T) -> typing.Tuple[bool, T]:
        return validate(v)
