import abc
import typing

from fiepipelib.gitlabserver.routines.gitlabserver import GitLabManagedTypeRoutines, GitLabServerRoutines
from fiepipelib.gitlabserver.shell.gitlabserver import GitLabServerShell
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T", bound=GitLabManagedTypeRoutines)


class AbstractLocalManagedTypeCommand(AbstractShell, typing.Generic[T]):
    _server_shell: GitLabServerShell

    def get_server_shell(self) -> GitLabServerShell:
        return self._server_shell

    def __init__(self, server_shell: GitLabServerShell):
        self._server_shell = server_shell
        super().__init__()

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AbstractLocalManagedTypeCommand, self).get_plugin_names_v1()
        ret.append("gitlabserver.localmanagedtype")
        return ret

    @abc.abstractmethod
    def get_routines(self) -> T:
        raise NotImplementedError()

    def get_server_username(self) -> str:
        return self.get_server_shell().get_server_routines().get_server().get_username()

    def items_complete(self, text, line, begidx, endidx):
        ret = []
        manager = self.get_routines().get_local_manager_routines()
        all_items = manager.GetAllItems()
        for item in all_items:
            if manager.ItemToName(item).startswith(text):
                ret.append(manager.ItemToName(item))
        return ret




class LocalManagedUserTypeCommand(AbstractLocalManagedTypeCommand[T], typing.Generic[T]):
    """Subclass to create a command for locally managed types that is scoped to the user's account."""

    def items_complete(self, text, line, begidx, endidx):
        return super().items_complete(text, line, begidx, endidx)

    def __init__(self, server_shell: GitLabServerShell):
        super().__init__(server_shell)

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(LocalManagedUserTypeCommand, self).get_plugin_names_v1()
        ret.append("gitlabserver.localmanagedtype.user")
        return ret

    def do_push_all(self, arg):
        self.do_coroutine(self.get_routines().push_all_routine(self.get_server_username()))

    def do_pull_all(self, arg):
        self.do_coroutine(self.get_routines().pull_all_routine(self.get_server_username()))

    complete_push = items_complete

    def do_push(self, arg):
        args = self.parse_arguments(arg)
        self.do_coroutine(self.get_routines().push_routine(self.get_server_username(), args))

    complete_pull = items_complete

    def do_pull(self, arg):
        args = self.parse_arguments(arg)
        self.do_coroutine(self.get_routines().pull_routine(self.get_server_username(), args))

    def do_init_local(self, arg):
        """Initializes an empty local worktree for this GitLab managed type source
        Usage: init_local"""
        self.do_coroutine(self.get_routines().init_local(self.get_server_username()))

    def do_delete_local(self,arg):
        """Deletes the worktree for this GitLab managed type source.
        Usage: delete_local"""
        self.do_coroutine(self.get_routines().delete_local(self.get_server_username()))


class LocalManagedGroupTypeCommand(AbstractLocalManagedTypeCommand[T], typing.Generic[T]):
    """Subclass to create a command for a locally managed type that takes group names at runtime
    to determine which group to pull from."""

    def __init__(self, server_routines: GitLabServerShell):
        super().__init__(server_routines)

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(LocalManagedGroupTypeCommand, self).get_plugin_names_v1()
        ret.append("gitlabserver.localmanagedtype.group")
        return ret

    def groupnames_complete(self, text, line, begidx, endidx) -> typing.List[str]:
        # TODO: Implement this at some point?
        return []

    complete_push_all = groupnames_complete

    def do_push_all(self, arg):
        """Pushes all items to a given gitlab group.
        Usage: push_all [groupname]
        arg groupname:  The name of the GitLab group to push to.
        """
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().push_all_routine(args[0]))

    complete_pull_all = groupnames_complete

    def do_pull_all(self, arg):
        """
        Pulls all items from a given gitlab group.
        Usage: pull_all [groupname]
        arg groupname:  The name of the GitLab group to pull from.
        """
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().pull_all_routine(args[0]))

    def pushpull_complete(self, text, line, begidx, endidx):
        self.index_based_complete(text, line, begidx, endidx, {1: self.groupnames_complete}, self.items_complete)

    complete_push = pushpull_complete

    def do_push(self, arg):
        """
        Push the given named items to the given GitLab group.
        Usage: push [groupname] [item] ... [item]
        arg groupname: the name of the GitLab group to push to.
        args item: any number of item names to push.
        """
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().push_routine(self.get_server_username(), args[1:]))

    complete_pull = pushpull_complete

    def do_pull(self, arg):
        """
        Pull the given named items from the given GitLab group.
        Usage: pull [groupname] [item] ... [item]
        arg groupname: the name of the GitLab group to pull from.
        args item: any number of item name to pull
        """
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().pull_routine(self.get_server_username(), args[1:]))

    complete_init_local = groupnames_complete

    def do_init_local(self, arg):
        """Initializes an empty local worktree for a given GitLab group's managed type
        Usage: init_local [groupname]
        arg groupname: The name of the GitLab group to init a local worktree for."""
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().init_local(args[0]))

    complete_delete_local = groupnames_complete

    def do_delete_local(self, arg):
        """Deletes the local worktree for a given GitLab group;s managed type
        Usage: delete_local [groupname]
        arg groupname: The name of the GitLab group to delete a local worktree for."""
        args = self.parse_arguments(arg)
        if len(args) < 1:
            self.perror("No group specified.")
            return
        self.do_coroutine(self.get_routines().delete_local(args[0]))
