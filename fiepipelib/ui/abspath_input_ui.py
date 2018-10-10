import typing
import pathlib
import abc

from fieui.InputModalUI import AbstractInputModalUI, T
from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI

def validate(v: str) -> typing.Tuple[bool,str]:
    p = pathlib.Path(v)
    if p.is_absolute():
        return True, v
    return False, v

class AbstractAbspathInputUI(AbstractInputModalUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        return validate(v)


class AbstractAbspathDefaultInputUI(AbstractInputDefaultModalUI[str]):

    def validate(self, v: T) -> typing.Tuple[bool, T]:
        return validate(v)
