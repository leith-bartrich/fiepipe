import sys
import typing

import fiepipelib.gitstorage.data.git_asset
import fiepipelib.gitstorage.data.git_root
import fiepipelib.gitstorage.data.git_working_asset
import fiepipelib.gitstorage.data.local_root_configuration
import fiepipelib.gitstorage.shells.gitroot
import fiepipelib.gitstorage.shells.roots_component
import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand
import fiepipelib.shells.AbstractShell
from fiepipelib.automanager.shell.automanager import GitLabServerModeChoiceShellUI, \
    ModalTrueFalseDefaultQuestionShellUI, GitLabServerNameShellModalInput
from fiepipelib.components.shells.component import AbstractComponentCommand
from fiepipelib.components.shells.component import AbstractComponentContainerShell
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fiepipelib.container.local_config.routines.automanager import \
    ContainerAutomanagerConfigurationComponentRoutinesInteractive
from fiepipelib.container.shared.routines.container import ContainerRoutines
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.container.local_config.routines.container import LocalContainerRoutines

class ContainerShell(fiepipelib.shells.AbstractShell.AbstractShell, AbstractComponentContainerShell):
    """A shell for working in a local container"""

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(ContainerShell, self).get_plugin_names_v1()
        ret.append('container')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_container_routines()
        routines.load()
        container = routines.get_container()
        name = container.GetShortName()
        return self.prompt_separator.join(['fiepipe', container.GetFQDN(), container.GetShortName()])

    _container_id_var: ContainerIDVariableCommand = None

    def get_container_id_var(self) -> ContainerIDVariableCommand:
        return self._container_id_var

    def __init__(self, container_id_var: ContainerIDVariableCommand):
        self._container_id_var = container_id_var
        super().__init__()
        self.add_variable_command(container_id_var, "container", [], False)
        roots_submenu = fiepipelib.gitstorage.shells.roots_component.RootsComponentCommand(self._container_id_var)
        self.add_submenu(roots_submenu, "roots", [])
        automanager_config_submenu = ContainerAutomanagerConfigurationCommand(self)
        self.add_submenu(automanager_config_submenu, "automanager_configuration", [])

    def get_container_routines(self) -> ContainerRoutines:
        return ContainerRoutines(self._container_id_var.get_value())

    def get_local_container_config_routines(self) -> LocalContainerRoutines:
        return LocalContainerRoutines(self._container_id_var.get_value())


class ContainerAutomanagerConfigurationCommand(AbstractComponentCommand[ContainerAutomanagerConfigurationComponent]):

    def get_container_shell(self) -> ContainerShell:
        ret = super().get_container_shell()
        assert isinstance(ret, ContainerShell)
        return ret

    def get_component_routines(self) -> ContainerAutomanagerConfigurationComponentRoutinesInteractive:
        cont_routines = self.get_container_shell().get_local_container_config_routines()
        return ContainerAutomanagerConfigurationComponentRoutinesInteractive(cont_routines)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(ContainerAutomanagerConfigurationCommand, self).get_plugin_names_v1()
        ret.append("fiepipe.automanager.container_config.command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self.get_container_shell().get_prompt_text(), "automanager_config"])

    def do_configure(self, args):
        """(re)configures the automanager for this container.

        Usage: configure"""
        routines = self.get_component_routines()
        self.do_coroutine(
            routines.reconfigure_routine(self.get_feedback_ui(), ModalTrueFalseDefaultQuestionShellUI(self),
                                         GitLabServerModeChoiceShellUI(self), GitLabServerNameShellModalInput(self)))

    def do_print(self, args):
        """prints the automanager configuration for this container

        Usage: print"""
        routines = self.get_component_routines()
        self.do_coroutine(routines.print_routine(self.get_feedback_ui()))

def main():
    container_var = ContainerIDVariableCommand("")
    if not container_var.set_from_args("container", sys.argv[1:], ""):
        print("No container id given. e.g. -container 89347589372589")
        exit(-1)
    shell = ContainerShell(container_var)
    shell.cmdloop()


if __file__ == "__main__":
    main()
