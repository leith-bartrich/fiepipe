import abc
import typing

from fiepipelib.components.data.components import AbstractNamedItemListComponent
from fiepipelib.components.routines.bound_component import AbstractBoundComponentRoutines
from fiepipelib.components.routines.component import AbstractNamedItemListComponentInteractiveRoutines

SC = typing.TypeVar("SC", bound=AbstractNamedItemListComponent)
LC = typing.TypeVar("LC", bound=AbstractNamedItemListComponent)


class AbstractNamedListBoundComponentRoutines(
    AbstractBoundComponentRoutines[
        AbstractNamedItemListComponentInteractiveRoutines[SC], AbstractNamedItemListComponentInteractiveRoutines[LC]],
    typing.Generic[SC, LC]):

    @abc.abstractmethod
    def get_shared_component_routines(self) -> AbstractNamedItemListComponentInteractiveRoutines[SC]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_component_routines(self) -> AbstractNamedItemListComponentInteractiveRoutines[LC]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_name_for_shared_name(self, name: str) -> str:
        raise NotImplementedError()

    def get_shared_item_names(self) -> typing.List[str]:
        return self.get_shared_component().get_names()

    def get_local_item_names(self) -> typing.List[str]:
        return self.get_local_component().get_names()

    def get_names_dict(self) ->typing.Dict[str,str]:
        ret = {}
        shared_names = self.get_shared_item_names()
        for shared_name in shared_names:
            ret[shared_name] = self.get_local_name_for_shared_name(shared_name)
        return ret


    def clear_local_item(self, shared_name: str):
        self.load()
        local_name = self.get_local_name_for_shared_name(shared_name)
        comp = self.get_local_component()
        comp.delete_by_name(local_name)
        self.commit()

    def remove_shared_item(self, name: str):
        self.clear_local_item(name)
        self.load()
        comp = self.get_shared_component()
        comp.delete_by_name(name)
        self.commit()

    async def create_local_component_data_routine(self):
        comp_routines = self.get_local_component_routines()
        cont_routines = comp_routines.get_container_routines()
        cont_routines.load()
        comp = self.get_local_component()

        if not comp.Exists():
            comp.Load()
            self.commit()

    async def create_shared_item_routine(self, name: str):
        self.load()
        shared_component = self.get_shared_component()
        try:
            item = shared_component.get_by_name(name)
            await self.get_shared_component_routines().create_update_item(name, item)
        except LookupError:
            item = await self.get_shared_component_routines().create_update_item(name, None)
            shared_component.GetItems().append(item)


        self.commit()

    async def create_local_item_routine(self, name: str):
        self.load()

        component = self.get_local_component()
        item_name = self.get_local_name_for_shared_name(name)

        try:
            item = self.get_local_component().get_by_name(item_name)
            await self.get_local_component_routines().create_update_item(item_name, item)
        except LookupError:
            item = await self.get_local_component_routines().create_update_item(item_name, None)
            component.GetItems().append(item)

        self.commit()

    def local_item_exists(self, name: str) -> bool:
        self.load()

        item_name = self.get_local_name_for_shared_name(name)

        try:
            item = self.get_local_component().get_by_name(item_name)
            return item is not None
        except LookupError:
            return False

