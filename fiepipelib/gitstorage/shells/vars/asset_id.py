import typing
import uuid

from fieuishell.ModalInputUI import InputModalShellUI
from fieuishell.Shell import VarCommand


class AssetIDInputModal(InputModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        try:
            return True, str(uuid.UUID(v))
        except ValueError:
            return False, v


class AssetIDVarCommand(VarCommand[str]):

    def __init__(self, initial_value: str = None):
        if initial_value is None:
            initial_value = str(uuid.uuid4())
        super().__init__(AssetIDInputModal(self), initial_value)

    def new_value(self):
        self.set_value(str(uuid.uuid4()))