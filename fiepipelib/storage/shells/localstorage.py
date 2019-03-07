import functools
import os.path
import typing

import cmd2

import fiepipelib.legalentity.authority.data.entity_authority
import fiepipelib.encryption.public.privatekey
import fiepipelib.shells.AbstractShell
import fiepipelib.storage.localvolume
from fiepipelib.storage.routines.localstorage import LocalStorageInteractiveRoutines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines


class Shell(fiepipelib.shells.AbstractShell.AbstractShell):
    _localUser = None
    _localStorageRoutines = None

    def __init__(self, localUser: LocalUserRoutines, localStorage: LocalStorageInteractiveRoutines):
        super().__init__()
        self._localUser = localUser
        self._localStorageRoutines = localStorage

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('local_storage')
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["pipe", "local_storage"])

    def fet_fork_args(self) -> typing.List[str]:
        return []

    def do_list_mounted_volumes(self, arg):
        volumes = self._localStorageRoutines.get_all_mounted_volumes()
        for vol in volumes:
            self.poutput(vol.GetName() + ": " + vol.GetPath() + "  [" + "] [".join(vol.GetAdjectives()) + "]")

    def do_list_configured_volumes(self, arg):
        volumes = self._localStorageRoutines.get_configured_volumes()
        for vol in volumes:
            self.poutput(vol.GetName() + ": " + vol.GetPath() + "  [" + "] [".join(vol.GetAdjectives()) + "]")

    def do_delete_configured_volume(self, arg):
        """Deletes the named configured storage.
        Usage: DeleteConfiguredVolume [name]
        arg name: the name of the configured storage to delete"""
        args = self.parse_arguments(arg)
        if len(args) == 0:
            self.perror("No storage specified.")
            return
        self.do_coroutine(self._localStorageRoutines.delete_configured_volume_routine(args[0]))

    complete_create_volume = functools.partial(cmd2.Cmd.path_complete)

    def do_create_volume(self, arg):
        """Creates a named configured volume.
        Usage: CreateConfiguredVolume [name] [path]
        arg name: the name of the new volume.  No spaces please.
        arg path: the absolute path of the new storage volume.  Spaces are allowed but always discouraged.
        """
        args = self.parse_arguments(arg)
        if len(args) == 0:
            self.perror("No name given.")
            return
        if len(args) == 1:
            self.perror("No path given.")
            return
        if not os.path.isabs(args[1]):
            print("Path must be absolute: " + args[1])
            return
        self.do_coroutine(self._localStorageRoutines.create_volume_routine(args[0], args[1]))

    def printAdjectives(self):
        self.do_coroutine(self._localStorageRoutines.print_adjectives_routine())

    def local_volumes_complete(self, text, line, begidx, endidx):
        ret = []
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        allVolumes = manager.GetAll()
        for vol in allVolumes:
            if vol.GetName().startswith(text):
                ret.append(vol.GetName())
        return ret

    complete_add_adjective = local_volumes_complete

    def do_add_adjective(self, arg):
        args = self.parse_arguments((arg))

        if len(args) == 0:
            self.perror(("No storage specified."))

        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        volumes = manager.GetByName(args[0])
        if len(volumes) == 0:
            self.perror("Volume not found: " + args[0])
            return

        volume = volumes[0]

        self.do_coroutine(self._localStorageRoutines.add_adjective_interactive_routine(volume))

    complete_delete_adjective = local_volumes_complete

    def do_delete_adjective(self, arg):
        args = self.parse_arguments(arg)
        if len(args) == 0:
            self.perror("No storage specified.")
            return
        manager = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        volumes = manager.GetByName(arg)
        if len(volumes) == 0:
            self.perror("Volume not found: " + arg)
            return
        volume = volumes[0]

        self.do_coroutine(self._localStorageRoutines.do_delete_adjective_interactive_routine(volume))

    def external_volume_paths_complete(self, text, line, begidx, endidx):

        ret = []
        platform = self._localUser.get_platform()

        if isinstance(platform, fiepipelib.localplatform.localplatformwindows):
            # windows logic.  drive letter paths.
            letters = platform.get_logical_drive_letters()
            for letter in letters:
                if letter.lower().startswith(text.lower()):
                    ret.append(letter + ":\\")
            return ret
        else:
            # on linux, we default to path completion
            return cmd2.path_complete(text, line, begidx, endidx)

    complete_setup_removable = external_volume_paths_complete

    def do_setup_removable(self, arg):
        args = self.parse_arguments(arg)
        if len(args) == 0:
            self.perror("No path specified.")
            return

        self.do_coroutine(self._localStorageRoutines.do_setup_removable(args[0]))
