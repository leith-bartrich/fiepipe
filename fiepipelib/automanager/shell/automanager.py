import typing

from fiepipelib.automanager.data.localconfig import LegalEntityConfig
from fiepipelib.automanager.data.localconfig import LegalEntityMode, GitLabServerMode
from fiepipelib.automanager.routines.automanager import AutoManagerInteractiveRoutines, LegalEntityModeChoiceUI, \
    GitlabServerModeCoiceUI, GitlabServerNameUI, LegalEntityInteractiveRoutines
from fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand import LocalManagedTypeCommand
from fiepipelib.shells.AbstractShell import AbstractShell
from fieui.InputModalUI import T
from fieuishell.EnumChoiceModal import EnumInputModalShellUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI
from fieuishell.Shell import VarCommand
from fieuishell.ModalTrueFalseDefaultQuestionUI import ModalTrueFalseDefaultQuestionShellUI

class LegalEntityModeChoiceShellUI(LegalEntityModeChoiceUI, EnumInputModalShellUI[LegalEntityMode]):

    def get_names(self) -> typing.List[str]:
        ret = []
        for v in LegalEntityMode:
            ret.append(v.name)
        return ret

    def to_value(self, text) -> (bool, LegalEntityMode):
        try:
            return True, LegalEntityMode[text]
        except KeyError:
            return False, LegalEntityMode.NONE


class GitLabServerModeChoiceShellUI(GitlabServerModeCoiceUI, EnumInputModalShellUI[GitLabServerMode]):

    def get_names(self) -> typing.List[str]:
        ret = []
        for v in GitLabServerMode:
            ret.append(v.name)
        return ret

    def to_value(self, text) -> (bool, T):
        try:
            return True, GitLabServerMode[text]
        except KeyError:
            return False, GitLabServerMode.AUTO


class GitLabServerNameShellModalInput(GitlabServerNameUI, InputDefaultModalShellUI[str]):
    pass


class AbstractSleepVarInputUI(InputModalShellUI[float]):

    def validate(self, v: str) -> typing.Tuple[bool, T]:
        try:
            ret = float(v)
            return True, ret
        except ValueError:
            return False, 0.0


class SleepVarCommand(VarCommand[float]):
    pass


class AutoManagerShell(AbstractShell):
    _sleep_var: SleepVarCommand = None

    def __init__(self):
        super().__init__()
        self._sleep_var = SleepVarCommand(AbstractSleepVarInputUI(self), 300.0)
        self.add_variable_command(self._sleep_var, "sleep", [], True)
        self.add_submenu(EntityConfigCommand(), "entity_config", [])

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AutoManagerShell, self).get_plugin_names_v1()
        ret.append("fiepipe.automanager.shell")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["fiepipe", "automanager"])

    def get_routines(self) -> AutoManagerInteractiveRoutines:
        return AutoManagerInteractiveRoutines(self._sleep_var.get_value())

    def do_run_once(self, args: str):
        """Runs the Auto-Management loop once"""
        automanager = self.get_routines()
        self.do_coroutine(automanager.main_routine(self.get_feedback_ui(), once=True))

    # def fqdn_complete(self, text, line, begidx, endidx):
    #     ret = []
    #     automanager = self.get_routines()
    #     all_fqdns = automanager.get_fqdns()
    #     for fqdn in all_fqdns:
    #         if fqdn.lower().startswith(text.lower()):
    #             ret.append(fqdn)
    #     return ret


class EntityConfigCommand(LocalManagedTypeCommand[LegalEntityConfig]):

    def get_routines(self) -> LegalEntityInteractiveRoutines:
        return LegalEntityInteractiveRoutines(self.get_feedback_ui(), LegalEntityModeChoiceShellUI(self),
                                              GitLabServerModeChoiceShellUI(self),
                                              GitLabServerNameShellModalInput(self),
                                              ModalTrueFalseDefaultQuestionShellUI(self))

    def get_shell(self, item) -> AbstractShell:
        return super(EntityConfigCommand, self).get_shell(item)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(EntityConfigCommand, self).get_plugin_names_v1()
        ret.append("fiepipe.automanager.entityconfig.command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(['fiepipe', 'automanager', 'entity_config'])
