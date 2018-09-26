import typing

from fieui.InputModalUI import T
from fieuishell.ModalInputUI import InputModalShellUI


class ContainerIDInputUI(InputModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        if v is None:
            return False, ""
        if v.isspace():
            return False, ""
        return True, v