from fiepipelib.components.routines.component_container import ComponentContainerRoutines
from fiepipelib.container.shared.data.container import Container, LocalContainerManager
from fiepipelib.localuser.routines.localuser import get_local_user_routines


class ContainerRoutines(ComponentContainerRoutines[Container]):
    _id: str = None

    def get_id(self) -> str:
        return self._id

    def __init__(self, id: str):
        super(ContainerRoutines, self).__init__()
        self._id = id

    def get_manager(self) -> LocalContainerManager:
        user = get_local_user_routines()
        return LocalContainerManager(user)

    _container: Container = None

    def get_container(self) -> Container:
        return self._container

    def commit(self):
        self.get_manager().Set([self.get_container()])

    def load(self):
        self._container = self.get_manager().GetByID(self.get_id())[0]
