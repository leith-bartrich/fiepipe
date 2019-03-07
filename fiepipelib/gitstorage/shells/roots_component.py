import typing

from fiepipelib.components.shells.component import AbstractNamedListBoundComponentCommand
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager
from fiepipelib.container.local_config.routines.container import LocalContainerRoutines
from fiepipelib.container.shared.routines.container import ContainerRoutines
from fiepipelib.gitstorage.data.git_root import SharedGitRootsComponent
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfigurationsComponent
from fiepipelib.gitstorage.routines.gitroots import RootsConfigurableComponentRoutines, SharedRootsComponentInteractiveRoutines, \
    LocalRootConfigsComponentInteractiveRoutines
from fiepipelib.gitstorage.shells.gitroot import Shell
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.shells.ui.subpath_input_ui import SubpathInputDefaultUI
from fiepipelib.storage.localvolume import localvolume
from fiepipelib.storage.routines.localstorage import LocalStorageInteractiveRoutines
from fieuishell.ChoiceInputModalUI import ChoiceInputModalShellUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitstorage.shells.vars.root_id import RootIDVarCommand
from fiepipelib.storage.routines.ui.volumes import NewVolumeNameInputUI
from fiepipelib.storage.shells.ui.volumes import NewVolumeNameShellInputUI

class RootNameInputUI(InputDefaultModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        if v is None:
            return False, ""
        if v.isspace():
            return False, ""
        return True, v


class RootDescInputUI(InputDefaultModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        if v is None:
            return False, ""
        if v.isspace():
            return False, ""
        return True, v


class ConfigurableVolumeNameInputUI(InputModalShellUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        if v is None:
            return False, ""
        if v.isspace():
            return False, ""
        return True, v


class RootsComponentCommand(
    AbstractNamedListBoundComponentCommand[SharedGitRootsComponent, LocalRootConfigurationsComponent]):
    _container_id_var: ContainerIDVariableCommand = None

    def __init__(self, container_id_var: ContainerIDVariableCommand):
        self.add_variable_command(container_id_var, "container", [], False)
        self._container_id_var = container_id_var
        super().__init__()

    def get_named_list_bound_component_routines(self) -> RootsConfigurableComponentRoutines:
        container_routines = ContainerRoutines(self._container_id_var.get_value())
        container_config_routines = LocalContainerRoutines(self._container_id_var.get_value())
        shared_routines = SharedRootsComponentInteractiveRoutines(container_routines, RootNameInputUI(self), RootDescInputUI(self))
        local_routines = LocalRootConfigsComponentInteractiveRoutines(container_config_routines,
                                                                      ChoiceInputModalShellUI[localvolume](self),
                                                                      SubpathInputDefaultUI(self), shared_routines)
        return RootsConfigurableComponentRoutines(shared_routines, local_routines)

    def get_shell(self, name) -> AbstractShell:
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        if not routines.local_item_exists(name):
            self.perror("Container not configured.  Cannot enter it.")
            raise LookupError("Container not configured.  Cannot enter it.")
        root_id = routines.get_local_name_for_shared_name(name)
        container_id = routines.get_container_routines().get_id()
        root_var = RootIDVarCommand(root_id)
        container_var = ContainerIDVariableCommand(container_id)
        return Shell(root_var,container_var)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(RootsComponentCommand, self).get_plugin_names_v1()
        ret.append('gitroots.component.command')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        container = routines.get_shared_component_routines().get_container_routines().get_container()
        fqdn = container.GetFQDN()
        container_name = container.GetShortName()
        return self.prompt_separator.join(['fiepipe', fqdn, container_name, "roots"])
