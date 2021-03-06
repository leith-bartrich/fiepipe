import typing
from abc import ABC

from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI
from fieui.InputModalUI import AbstractInputModalUI, T


def validate(v: str) -> typing.Tuple[bool, str]:
    if v == "":
        return False, ""
    if v is None:
        return False, ""
    return True, v


class GitLabUsernameInputDefaultUI(AbstractInputDefaultModalUI[str], ABC):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        return validate(v)


class GitLabUsernameInputUI(AbstractInputModalUI[str], ABC):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        return validate(v)
