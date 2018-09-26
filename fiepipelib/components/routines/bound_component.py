import abc
import typing

from fiepipelib.components.data.components import AbstractComponent
from fiepipelib.components.routines.component import AbstractComponentRoutines

SR = typing.TypeVar('SR', bound=AbstractComponentRoutines)
LR = typing.TypeVar('LR', bound=AbstractComponentRoutines)

SC = typing.TypeVar('SC', bound=AbstractComponent)
LC = typing.TypeVar('LC', bound=AbstractComponent)


class AbstractBoundComponentRoutines(typing.Generic[SC, LC]):
    """Abstract generic routines for a component that has both
    a [shared] container component 'SC' and a local configuration component 'LC'."""

    @abc.abstractmethod
    def get_shared_component_routines(self) -> AbstractComponentRoutines[SC]:
        """Returns the routines for the shared component"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_component_routines(self) -> AbstractComponentRoutines[LC]:
        """Returns the routines for the local component"""
        raise NotImplementedError()

    def get_local_component(self) -> LC:
        return self.get_local_component_routines().get_component()

    def get_shared_component(self) -> SC:
        return self.get_shared_component_routines().get_component()

    def clear_local_component_data(self):
        """Removes all the local component data.
        This removes the whole component's data, not just parts of it."""
        comp_routines = self.get_local_component_routines()
        cont_routines = comp_routines.get_container_routines()
        cont_routines.load()
        comp = comp_routines.get_component()
        comp.Clear()
        cont_routines.commit()

    @abc.abstractmethod
    async def create_local_component_data_routine(self):
        """Configures/creates the local component data."""
        raise NotImplementedError()

    def load(self):
        #order is important since they could share the same container.
        #we load all containers before loading components.
        self.get_shared_component_routines().get_container_routines().load()
        self.get_local_component_routines().get_container_routines().load()
        self.get_shared_component_routines().load()
        self.get_local_component_routines().load()

    def commit(self):
        #order is important since they could share the same containers.
        #we commit all components before commiting the containers.
        self.get_local_component_routines().commit()
        self.get_shared_component_routines().commit()
        self.get_local_component_routines().get_container_routines().commit()
        self.get_shared_component_routines().get_container_routines().commit()
