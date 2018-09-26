import typing

from fieui.InputModalUI import T
from fieuishell.ModalInputUI import InputModalShellUI


class ContainerIDInputModalUI(InputModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        # TODO: Better validate this.
        if v.isspace():
            return False, v
        else:
            return True, v