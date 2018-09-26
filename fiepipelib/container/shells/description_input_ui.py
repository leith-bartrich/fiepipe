import typing

from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI


class DescriptionInputUI(InputDefaultModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        return True, v