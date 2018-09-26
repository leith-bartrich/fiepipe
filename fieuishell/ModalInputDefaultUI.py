import asyncio
import typing
from abc import ABC

import fieui.InputDefaultModalUI

T = typing.TypeVar("T")


class InputDefaultModalShellUI(fieui.InputDefaultModalUI.AbstractInputDefaultModalUI[T], ABC):
    _shell = None

    def __init__(self, shell: "Shell"):
        self._shell = shell

    async def execute(self, question: str, default: str) -> T:
        try:
            while True:
                i = str(self._shell.pseudo_raw_input(question + "[" + default + "]: "))
                if i.isspace() or (i == "") or (i is None):
                    i = default
                validated = self.validate(i)
                if validated[0]:
                    return validated[1]
        except KeyboardInterrupt as ki:
            self._shell.get_feedback_ui().warn("User canceled.")
            raise asyncio.CancelledError()
