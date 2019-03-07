import asyncio
import typing
import enum
import abc

from fieui.AbstractEnumChoiceModal import AbstractEnumChoiceModal, T
from fieuishell.Shell import Shell


class EnumInputModalShellUI(AbstractEnumChoiceModal[T]):

    _shell: Shell = None

    def __init__(self, shell: Shell):
        self._shell = shell

    def _print_color(self, message: str, color: str):
        colorized = self._shell.colorize(message, color)
        self._print(colorized)

    def _print(self, message: str):
        self._shell.poutput(message)

    @abc.abstractmethod
    def get_names(self) -> typing.List[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def to_value(self, text) -> (bool, T):
        raise NotImplementedError()

    async def execute(self, question: str) -> T:
        names = self.get_names()

        try:
            while True:
                self._print_color("Choose: " + question + " [enter to list]", "blue")
                r = str(self._shell.pseudo_raw_input(": "))
                if r.strip() == "":
                    for name in names:
                        self._print("  " + name)
                else:
                    match, val = self.to_value(r)
                    if match:
                        return val
        except KeyboardInterrupt as ki:
            await self._shell.get_feedback_ui().warn("User canceled.")
            raise asyncio.CancelledError

