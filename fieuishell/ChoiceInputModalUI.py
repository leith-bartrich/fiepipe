import asyncio
import typing

from fieui.ChoiceInputModalUI import AbstractChoiceInputModalUI, T
from fieuishell.Shell import Shell


class ChoiceInputModalShellUI(AbstractChoiceInputModalUI[T]):
    _shell: Shell = None

    def __init__(self, shell: Shell):
        self._shell = shell

    def _print_color(self, message: str, color: str):
        colorized = self._shell.colorize(message, color)
        self._print(colorized)

    def _print(self, message: str):
        self._shell.poutput(message)

    async def execute(self, question: str, choices: typing.Dict[str,T]) -> typing.Tuple[str, T]:
        try:
            while True:
                self._print_color("Choose: " + question + " [enter to list]", "blue")
                r = str(self._shell.pseudo_raw_input(": "))
                if r.strip() == "":
                    for name in choices.keys():
                        self._print("  " + name)
                else:
                    for possible in choices.keys():
                        if possible.lower() == r.lower():
                            return possible, choices[possible]
        except KeyboardInterrupt as ki:
            await self._shell.get_feedback_ui().warn("User canceled.")
            raise asyncio.CancelledError
