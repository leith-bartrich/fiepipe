import asyncio

from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class ModalTrueFalseDefaultQuestionShellUI(AbstractModalTrueFalseDefaultQuestionUI):
    _shell = None

    def __init__(self, shell: "Shell"):
        self._shell = shell

    async def execute(self, question: str, tname: str = "Y", fname: str = "N", cname: str = "C",
                      default: bool = False) -> bool:

        default_text = fname
        if default:
            default_text = tname

        while True:
            r = str(self._shell.pseudo_raw_input(
                question + " (" + tname + ":" + fname + ":" + cname + ")[" + default_text + "]: "))
            if (r.lower() == tname.lower()):
                return True
            elif (r.lower() == fname.lower()):
                return False
            elif (r.lower() == cname.lower()):
                raise asyncio.CancelledError()
            elif (r.isspace() or (r == "") or (r is None)):
                return default
