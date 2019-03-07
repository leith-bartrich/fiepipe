import abc
import typing

from fiepipelib.components.data.components import AbstractComponent, AbstractItemListComponent, AbstractNamedItemListComponent
from fiepipelib.components.routines.component_container import ComponentContainerRoutines

CT = typing.TypeVar('CT', bound=AbstractComponent)


class AbstractComponentRoutines(typing.Generic[CT]):
    """Abstract generic routines for addressing a component 'CT' of a Container"""

    _component_container_routines: ComponentContainerRoutines = None

    def __init__(self, component_container_routines: ComponentContainerRoutines):
        """Can be used for either a container or a configured container.
        """
        self._component_container_routines = component_container_routines

    def get_container_routines(self) -> ComponentContainerRoutines:
        return self._component_container_routines

    @abc.abstractmethod
    def new_component(self)-> CT:
        raise NotImplementedError()

    _component: CT = None

    def get_component(self) -> CT:
        return self._component

    def load(self):
        comp = self.new_component()
        self._component = comp
        comp.Load()

    def commit(self):
        self.get_component().Commit()



I = typing.TypeVar("I")


class AbstractItemListComponentInteractiveRoutines(AbstractComponentRoutines[AbstractItemListComponent[I]], typing.Generic[I]):


    @abc.abstractmethod
    async def create_empty_item(self) -> I:
        raise NotImplementedError()

    @abc.abstractmethod
    async def update_item(self, item: I):
        raise NotImplementedError()

    async def create_update_item(self, item: I = None) -> I:
        if item is None:
            item = self.create_empty_item()
        await self.update_item(item)
        return item

class AbstractNamedItemListComponentRoutines(AbstractComponentRoutines[AbstractNamedItemListComponent[I]], typing.Generic[I]):

    def get_named_item(self,name:str) -> I:
        return self.get_component().get_by_name(name)

class AbstractNamedItemListComponentInteractiveRoutines(AbstractNamedItemListComponentRoutines[I]):


    @abc.abstractmethod
    async def create_empty_item(self, name:str) -> I:
        raise NotImplementedError()

    @abc.abstractmethod
    async def update_item(self, item: I, name:str):
        raise NotImplementedError()

    async def create_update_item(self, name: str, item: I = None) -> I:
        if item is None:
            item = await self.create_empty_item(name)
        await self.update_item(item, name)
        return item

