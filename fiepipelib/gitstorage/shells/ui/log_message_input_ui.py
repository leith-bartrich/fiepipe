import typing

from fieui.InputModalUI import T
from fieuishell.ModalInputUI import InputModalShellUI


class LogMessageInputUI(InputModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        if v is None:
            return False, ""
        if len(v.strip()) == 0:
            return False, ""
        return True, v