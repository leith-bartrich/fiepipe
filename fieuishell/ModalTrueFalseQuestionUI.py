import asyncio

from fieui.ModalTrueFalseQuestionUI import AbstractModalTrueFalseQuestionUI


class ModalTrueFalseQuestionShellUI(AbstractModalTrueFalseQuestionUI):
    _shell = None

    def __init__(self, shell: "Shell"):
        self._shell = shell

    async def execute(self, question: str, tname: str = "Y", fname: str = "N", cname: str = "C") -> bool:
        while True:
            r = str(self._shell.pseudo_raw_input(
                question + " (" + tname + ":" + fname + ":" + cname + "): "))
            if (r.lower() == tname.lower()):
                return True
            elif (r.lower() == fname.lower()):
                return False
            elif (r.lower() == cname.lower()):
                raise asyncio.CancelledError()
