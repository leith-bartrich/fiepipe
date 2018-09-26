from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfiguration, \
    LocalContainerConfigurationManager, config_from_parameters
from fiepipelib.components.routines.component_container import ComponentContainerRoutines


class LocalContainerRoutines(ComponentContainerRoutines[LocalContainerConfiguration]):
    _container_id: str = None
    _manager: LocalContainerConfigurationManager = None

    def get_manager(self):
        return self._manager

    _container: LocalContainerConfiguration = None

    def get_container(self) -> LocalContainerConfiguration:
        return self._container

    def __init__(self, container_id: str, manager: LocalContainerConfigurationManager):
        self._container_id = container_id
        self._manager = manager

    def commit(self):
        self.get_manager().Set([self.get_container()])

    def load(self):
        try:
            self._container = self.get_manager().GetByID(self._container_id)[0]
        except LookupError:
            self._container = config_from_parameters(self._container_id)
