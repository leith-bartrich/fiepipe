import abc
import asyncio
import typing
import  json

from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedRoutines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T")


class LocalManagedTypeCommand(AbstractShell, typing.Generic[T]):
    """Abstract command for working with locally managed types in a CRUD type manner.
    """


    @abc.abstractmethod
    def get_routines(self) -> AbstractLocalManagedRoutines[T]:
        raise NotImplementedError()

    def get_user(self) -> LocalUserRoutines:
        return LocalUserRoutines(get_local_platform_routines())

    def do_list(self, args):
        """Lists all items.

        Usage: list
        """
        allitems = self.get_routines().GetAllItems()
        for i in allitems:
            self.poutput(self.get_routines().ItemToName(i))

    def type_complete(self, text, line, begidx, endidx):

        allitems = self.get_routines().GetAllItems()

        ret = []

        for i in allitems:
            name = self.get_routines().ItemToName(i)
            if name.startswith(text):
                ret.append(name)

        return ret

    complete_create_update = type_complete

    def do_create_update(self, args):
        """Used to create an item.  Often an interactive process.
        Usually, if the item already exists, the creation routine
        will allow one to modify it.

        Usage: create [name]

        arg name:  The name of the item to create.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        try:
            self.do_coroutine(self.get_routines().CreateUpdateRoutine(args[0]))
        except asyncio.CancelledError as ce:
            self.pfeedback("User canceled.")


    complete_delete = type_complete

    def do_delete(self, args):
        """Deletes the given item.

        Usage: delete [name]

        arg name: The name of the item to delete.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        try:
            self.do_coroutine(self.get_routines().DeleteRoutine(args[0]))
        except asyncio.CancelledError as ce:
            self.pfeedback("User canceled.")

    complete_enter = type_complete

    @abc.abstractmethod
    def get_shell(self, item) -> AbstractShell:
        """Override this.  Return an instantiated shell for the given item."""
        raise NotImplementedError()

    def do_enter(self, args):
        """Enters a shell for working with the given item.

        Usage: enter [name]

        arg name: The name of the item to enter.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        item = self.get_routines().GetItemByName(args[0])
        shell = self.get_shell(item)
        shell.cmdloop()

    complete_print = type_complete

    def do_print(self, args):
        """Prints a human readable version of the given named item to the screen.

        Usage: print [name]

        arg name: The name of the item to print.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        item = self.get_routines().GetItemByName(args[0])
        routines = self.get_routines()
        data = routines.GetManager().ToJSONData(item)
        to_print = json.dumps(data, indent=4, sort_keys=True)
        self.poutput(to_print)
