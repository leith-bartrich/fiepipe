import os
import os.path

from fiepipelib.container.shared.data.container import Container
from fiepipelib.gitstorage.data.git_root import SharedGitRootsComponent, GenerateNewID, RootFromParameters, GitRoot
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfigurationsComponent, \
    LocalRootConfigFromParameters, LocalRootConfiguration
from fiepipelib.components.routines.component import AbstractNamedItemListComponentRoutines
from fiepipelib.components.routines.component_container import ComponentContainerRoutines
from fiepipelib.storage.routines.localstorage import LocalStorageRoutines
from fiepipelib.components.routines.named_list_bound_component import AbstractNamedListBoundComponentRoutines
from fiepipelib.storage.localvolume import CommonAdjectives
from fiepipelib.ui.subpath_input_ui import AbstractSubpathDefaultInputUI
from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI
from fieui.ChoiceInputModalUI import AbstractChoiceInputModalUI
from fiepipelib.storage.localvolume import localvolume
from fiepipelib.storage.routines.ui.volumes import get_local_volume_choices
from fiepipelib.container.shared.routines.container import ContainerRoutines
from fiepipelib.container.local_config.routines.container import LocalContainerRoutines

class SharedRootsComponentRoutines(AbstractNamedItemListComponentRoutines[GitRoot]):
    def get_container_routines(self) -> ContainerRoutines:
        return super().get_container_routines()

    _name_input_ui = AbstractInputDefaultModalUI[str]
    _desc_input_ui = AbstractInputDefaultModalUI[str]

    def __init__(self, component_container_routines: ContainerRoutines,
                 name_input_ui: AbstractInputDefaultModalUI[str], desc_input_ui: AbstractInputDefaultModalUI[str]):
        super().__init__(component_container_routines)
        self._name_input_ui = name_input_ui
        self._desc_input_ui = desc_input_ui

    async def create_empty_item(self, name: str) -> GitRoot:
        new_id = GenerateNewID()
        return RootFromParameters(new_id, name, "A git storage root.")

    async def update_item(self, item: GitRoot, name: str):
        item._name = await self._name_input_ui.execute("Root name", item.GetName())
        item._description = await self._desc_input_ui.execute("Description", item.GetDescription())

    def new_component(self) -> SharedGitRootsComponent:
        cont_routines = self.get_container_routines()
        cont = cont_routines.get_container()
        return SharedGitRootsComponent(cont)


class LocalRootConfigsComponentRoutines(AbstractNamedItemListComponentRoutines[LocalRootConfiguration]):

    def get_container_routines(self) -> LocalContainerRoutines:
        return super().get_container_routines()

    _shared_component_routines: SharedRootsComponentRoutines = None



    def get_shared_component_routines(self) -> SharedRootsComponentRoutines:
        return self._shared_component_routines

    _local_storage_routines: LocalStorageRoutines = None

    def get_local_storage_routines(self) -> LocalStorageRoutines:
        return self._local_storage_routines

    _local_volume_choice_ui: AbstractChoiceInputModalUI[localvolume] = None
    _subpath_input_ui: AbstractSubpathDefaultInputUI = None

    def get_local_volume_choice_ui(self) -> AbstractChoiceInputModalUI[localvolume]:
        return self._local_volume_choice_ui

    def get_subpath_input_ui(self) -> AbstractSubpathDefaultInputUI:
        return self._subpath_input_ui

    def __init__(self, component_container_routines: LocalContainerRoutines,
                 local_storage_routines: LocalStorageRoutines,
                 local_volume_choice_ui: AbstractChoiceInputModalUI[localvolume],
                 subpath_input_ui: AbstractSubpathDefaultInputUI,
                 shared_component_routines: SharedRootsComponentRoutines
                 ):
        super().__init__(component_container_routines)
        self._local_storage_routines = local_storage_routines
        self._local_volume_choice_ui = local_volume_choice_ui
        self._subpath_input_ui = subpath_input_ui
        self._shared_component_routines = shared_component_routines

    async def create_empty_item(self, name: str) -> LocalRootConfiguration:
        home_vol = self.get_local_storage_routines().get_home_volume()
        shared_container_routines = self.get_shared_component_routines()
        shared_container = shared_container_routines.get_container_routines().get_container()
        assert isinstance(shared_container, Container)
        root_name = name
        for i in self.get_shared_component_routines().get_component().GetItems():
            if i.GetID() == name:
                root_name = i.GetName()
        return LocalRootConfigFromParameters(name, home_vol.GetName(), os.path.join(shared_container.GetFQDN(),
                                                                                    shared_container.GetShortName(),
                                                                                    root_name))

    async def update_item(self, item: LocalRootConfiguration, name: str):
        choices = get_local_volume_choices([CommonAdjectives.containerrole.WORKING_VOLUME])
        localVolumeName, localVolume = await self._local_volume_choice_ui.execute("Local volume", choices )

        item._volumeName = localVolume.GetName()

        subpath = await self.get_subpath_input_ui().execute("Sub-path of working directory",
                                                            item.GetWorkingSubPath())
        item._subPath = subpath

    def new_component(self) -> LocalRootConfigurationsComponent:
        cont_routines = self.get_container_routines()
        cont = cont_routines.get_container()
        return LocalRootConfigurationsComponent(cont)


class RootsConfigurableComponentRoutines(
    AbstractNamedListBoundComponentRoutines[SharedGitRootsComponent, LocalRootConfigurationsComponent]):
    _shared_roots_component_routines: SharedRootsComponentRoutines = None
    _local_root_configs_component_routines: LocalRootConfigsComponentRoutines = None

    def get_shared_component_routines(self) -> SharedRootsComponentRoutines:
        return self._shared_roots_component_routines

    def get_local_component_routines(self) -> LocalRootConfigsComponentRoutines:
        return self._local_root_configs_component_routines

    def get_container_routines(self) -> ContainerRoutines:
        return self._shared_roots_component_routines.get_container_routines()

    def __init__(self, shared_component_routines: SharedRootsComponentRoutines,
                 local_component_routines: LocalRootConfigsComponentRoutines):
        self._shared_roots_component_routines = shared_component_routines
        self._local_root_configs_component_routines = local_component_routines
        super(RootsConfigurableComponentRoutines, self).__init__()

    def get_local_name_for_shared_name(self, name: str) -> str:
        return self.get_shared_component().get_by_name(name).GetID()
