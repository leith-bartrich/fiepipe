from fiepipelib.ui.abspath_input_ui import AbstractAbspathInputUI, AbstractAbspathDefaultInputUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


class AbspathInputUI(AbstractAbspathInputUI, InputModalShellUI[str]):
    pass


class AbspathInputDefaultUI(AbstractAbspathDefaultInputUI, InputDefaultModalShellUI[str]):
    pass
