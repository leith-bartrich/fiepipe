from fiepipelib.ui.fileext_input_ui import AbstractFileExtDefaultInputUI, AbstractFileExtInputUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


class FileExtInputUI(AbstractFileExtInputUI, InputModalShellUI[str]):
    pass


class FileExtInputDefaultUI(AbstractFileExtDefaultInputUI, InputDefaultModalShellUI[str]):
    pass
