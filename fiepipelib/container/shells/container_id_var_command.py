from fiepipelib.container.shells.container_id_input_modal_ui import ContainerIDInputModalUI
from fieuishell.Shell import VarCommand


class ContainerIDVariableCommand(VarCommand[str]):

    def __init__(self, initial_value: str):
        super().__init__(ContainerIDInputModalUI(self), initial_value)