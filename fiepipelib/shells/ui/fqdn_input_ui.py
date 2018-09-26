import typing

from fieui.InputModalUI import T
from fieuishell.ModalInputUI import InputModalShellUI


class FQDNInputUI(InputModalShellUI):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        # TODO: better validate this.
        return True, v