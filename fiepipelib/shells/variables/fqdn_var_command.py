import fieuishell.Shell
from fieui.InputModalUI import T
from fiepipelib.shells.ui.fqdn_input_ui import FQDNInputUI


class FQDNVarCommand(fieuishell.Shell.VarCommand[str]):

    def __init__(self, initial_value: T = "*"):
        super().__init__(FQDNInputUI(self), initial_value)

    def is_any(self) -> bool:
        return self.get_value() == "*"

    def do_clear(self, args):
        self.set_value("*")


