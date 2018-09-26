import abc
import typing
from abc import ABC

from fiepipelib.components.data.components import AbstractComponent, AbstractNamedItemListComponent
from fiepipelib.components.routines.bound_component import AbstractBoundComponentRoutines
from fiepipelib.components.routines.component import AbstractComponentRoutines
from fiepipelib.components.routines.component_container import ComponentContainerRoutines
from fiepipelib.components.routines.named_list_bound_component import AbstractNamedListBoundComponentRoutines
from fiepipelib.shells.AbstractShell import AbstractShell


class AbstractComponentContainerShell(ABC):

    @abc.abstractmethod
    def get_container_routines(self) -> ComponentContainerRoutines:
        raise NotImplementedError()


C = typing.TypeVar("C", bound=AbstractComponent)


class AbstractComponentCommand(AbstractShell, typing.Generic[C]):
    _container_shell: AbstractComponentContainerShell = None

    def __init__(self, container_shell: AbstractComponentContainerShell):
        self._container_shell = container_shell
        super().__init__()

    @abc.abstractmethod
    def get_component_routines(self) -> AbstractComponentRoutines[C]:
        raise NotImplementedError()


SC = typing.TypeVar("SC", bound=AbstractComponent)
LC = typing.TypeVar("LC", bound=AbstractComponent)


class AbstractBoundComponentCommand(AbstractShell, typing.Generic[SC, LC], ABC):
    _container_shell: AbstractComponentContainerShell = None

    def __init__(self, container_shell: AbstractComponentContainerShell):
        self._container_shell = container_shell
        super().__init__()

    def get_bound_component_routines(self) -> AbstractBoundComponentRoutines[SC, LC]:
        raise NotImplementedError()


NLSC = typing.TypeVar("NLSC", bound=AbstractNamedItemListComponent)
NLLC = typing.TypeVar("NLLC", bound=AbstractNamedItemListComponent)


class AbstractNamedListBoundComponentCommand(AbstractShell, typing.Generic[NLSC, NLLC]):

    def __init__(self):
        super().__init__()

    def get_named_list_bound_component_routines(self) -> AbstractNamedListBoundComponentRoutines[NLSC, NLLC]:
        raise NotImplementedError()

    def item_names_complete(self, text, line, begidx, endidx):
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        shared_routines = routines.get_shared_component_routines()
        shared_component = shared_routines.get_component()
        shared_items = shared_component.GetItems()
        ret = []
        for item in shared_items:
            name = shared_component.item_to_name(item)
            if name.startswith(text):
                ret.append(name)
        return ret

    complete_configure = item_names_complete

    def do_configure(self, args):
        """(Re)Configures the given shared item.
        Usage: configure [name]

        arg name:  The name of the shared item to (re)configure."""
        args = self.parse_arguments(args)
        if len(args) < 1:
            self.perror("No name given.")
            return

        self.do_coroutine(self.get_named_list_bound_component_routines().create_local_item_routine(args[0]))

    complete_unconfigure = item_names_complete

    def do_unconfigure(self, args):
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        routines = self.get_named_list_bound_component_routines()
        routines.clear_local_item(args[0])

    def do_create(self, args):
        """(Re)Creates a shared item.
        Usage: create [name]

        arg name: The name of the shared tiem to (re)create.
        """

        args = self.parse_arguments(args)

        if len(args) < 1:
            self.perror("No name given.")
            return

        self.do_coroutine(self.get_named_list_bound_component_routines().create_shared_item_routine(args[0]))

    def do_list(self, args):
        """Lists the shared items.
        Usage: list"""
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        shared_routines = routines.get_shared_component_routines()
        shared_component = shared_routines.get_component()
        all_items = shared_component.GetItems()
        for item in all_items:
            self.poutput(shared_component.item_to_name(item))


    complete_is_configured = item_names_complete

    def do_is_configured(self, args):
        """Prints 'yes' or 'no' depending on whether the item has a local configuration or not.
        Usage: is_configured [name]
        arg name:  The name of the item to check.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        routines = self.get_named_list_bound_component_routines()
        if routines.local_item_exists(args[0]):
            self.poutput(self.colorize('yes','green'))
        else:
            self.poutput(self.colorize('no','yellow'))

    @abc.abstractmethod
    def get_shell(self, name) -> AbstractShell:
        self.perror("This command doesn't currently provide a shell type to enter.")
        raise NotImplementedError()

    complete_enter = item_names_complete

    def do_enter(self, args):
        """Enters a shell for the given item.
        Usage: enter [name]
        arg name: The name of the item to enter."""
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        shell = self.get_shell(args[0])
        shell.cmdloop()

    complete_delete = item_names_complete

    def do_delete(self, args):
        """Deletes the given item.
        Usage delete [name]
        arg name: The name of the item to delete."""
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        routines = self.get_named_list_bound_component_routines()
        routines.remove_shared_item(args[0])

    complete_print_shared = item_names_complete

    def do_print_shared(self, args):
        """Prints a shared item.
        Usage print_shared [name]
        arg name: The name of the item to print"""
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        shared_comp = routines.get_shared_component()
        item = shared_comp.get_by_name(args[0])
        data = shared_comp.ItemToJSONData(item)
        self.print_json_data(data)

    complete_print_local_configuration = item_names_complete

    def do_print_local_configuration(self, args):
        """Prints a local item's configuration.
        Usage print_local_configuration [name]
        arg name: The name of the item to print

        Will error if there is no local configuration item."""
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        routines = self.get_named_list_bound_component_routines()
        routines.load()
        if not routines.local_item_exists(args[0]):
            self.perror("Item not locally configured.")
        local_name = routines.get_local_name_for_shared_name(args[0])
        local_comp = routines.get_local_component().get_by_name(local_name)
        data = routines.get_local_component().ItemToJSONData(local_comp)
        self.print_json_data(data)






