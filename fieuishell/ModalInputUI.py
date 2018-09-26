import asyncio
import typing

import fieui.InputModalUI

T = typing.TypeVar("T")


class InputModalShellUI(fieui.InputModalUI.AbstractInputModalUI[T]):
    _shell = None

    def __init__(self, shell: "Shell"):
        self._shell = shell

    async def execute(self, question: str) -> T:
        try:
            while True:
                i = str(self._shell.pseudo_raw_input(question + ": "))
                validated = self.validate(i)
                if validated[0]:
                    return validated[1]
        except KeyboardInterrupt as ki:
            self._shell.get_feedback_ui().warn("User canceled.")
            raise asyncio.CancelledError()
