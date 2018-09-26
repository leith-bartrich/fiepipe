from fiepipelib.ui.subpath_input_ui import AbstractSubpathInputUI, AbstractSubpathDefaultInputUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


class SubpathInputUI(AbstractSubpathInputUI, InputModalShellUI[str]):
    pass


class SubpathInputDefaultUI(AbstractSubpathDefaultInputUI, InputDefaultModalShellUI[str]):
    pass
