import typing

from fiepipelib.components.shells.component import AbstractNamedListBoundComponentCommand
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager
from fiepipelib.container.local_config.routines.container import LocalContainerRoutines
from fiepipelib.container.shared.routines.container import ContainerRoutines
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitstorage.data.git_root import SharedGitRootsComponent
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfigurationsComponent
from fiepipelib.gitstorage.routines.gitroots import RootsConfigurableComponentRoutines, SharedRootsComponentRoutines, \
    LocalRootConfigsComponentRoutines
from fiepipelib.gitstorage.shells.gitroot import Shell
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.shells.ui.subpath_input_ui import SubpathInputDefaultUI
from fiepipelib.storage.localvolume import localvolume
from fiepipelib.storage.routines.localstorage import LocalStorageRoutines
from fieuishell.ChoiceInputModalUI import ChoiceInputModalShellUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


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
        plat_routines = get_local_platform_routines()
        user_routines = LocalUserRoutines(plat_routines)
        container_routines = ContainerRoutines(self._container_id_var.get_value())
        container_config_routines = LocalContainerRoutines(self._container_id_var.get_value(),
                                                           LocalContainerConfigurationManager(user_routines))
        local_storage_routines = LocalStorageRoutines(user_routines, self.get_feedback_ui(),
                                                      ChoiceInputModalShellUI(self),
                                                      ConfigurableVolumeNameInputUI(self))
        shared_routines = SharedRootsComponentRoutines(container_routines, RootNameInputUI(self), RootDescInputUI(self))

        local_routines = LocalRootConfigsComponentRoutines(container_config_routines, local_storage_routines,
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
        return Shell(root_id, container_id)

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