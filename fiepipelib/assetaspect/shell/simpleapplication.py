import abc
import os
import os.path
import typing

from fiepipelib.assetaspect.data.simpleapplication import AbstractSimpleApplicationInstall
from fiepipelib.assetaspect.routines.simpleapplication import AbstractSimpleApplicationInstallInteractiveRoutines, \
    AbstractSimpleFiletypeAspectConfigurationRoutines
from fiepipelib.assetaspect.shell.config import AssetConfigCommand
from fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand import LocalManagedTypeCommand
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T", bound=AbstractSimpleApplicationInstall)


class AbstractSimpleApplicationCommand(LocalManagedTypeCommand[T]):

    @abc.abstractmethod
    def get_routines(self) -> AbstractSimpleApplicationInstallInteractiveRoutines[T]:
        raise NotImplementedError()

    def get_shell(self, item) -> AbstractShell:
        return super(AbstractSimpleApplicationCommand, self).get_shell(item)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AbstractSimpleApplicationCommand, self).get_plugin_names_v1()
        app_name = self.get_routines().GetManager().get_application_name()
        ret.append(app_name + "_installs_command")
        return ret

    def get_prompt_text(self) -> str:
        app_name = self.get_routines().GetManager().get_application_name()
        return self.prompt_separator.join(['fiepipe', app_name + '_installs'])


class AbstractSimpleFiletypeConfigCommand(AssetConfigCommand[T]):



    @abc.abstractmethod
    def get_configuration_routines(self) -> AbstractSimpleFiletypeAspectConfigurationRoutines[T]:
        raise NotImplementedError()

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AbstractSimpleFiletypeConfigCommand, self).get_plugin_names_v1()
        ret.append('simplefiletype_aspectconfig_command')
        return ret

    def do_list_files(self, args):
        """Prints a list of openable files in the asset.

        Usage: list_files
        """
        routines = self.get_configuration_routines()
        routines.load()
        all_paths = routines.get_file_paths()
        asset_path = routines.get_asset_path()
        for file_path in all_paths:
            rel_path = os.path.relpath(file_path, asset_path)
            self.poutput(rel_path)

    def file_complete(self, text, line, begidx, endidx):
        ret = []
        routines = self.get_configuration_routines()
        routines.load()
        all_paths = routines.get_file_paths()
        asset_path = routines.get_asset_path()
        for file_path in all_paths:
            rel_path = os.path.relpath(file_path, asset_path)
            if rel_path.lower().startswith(text.lower()):
                ret.append(rel_path)
        return ret

    def install_complete(self, text, line, begidx, endidx):
        ret = []
        installs = self.get_configuration_routines().get_installs()
        for install in installs:
            if install.get_name().startswith(text):
                ret.append(install.get_name())
        return ret

    def complete_open(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx, {1: self.install_complete}, self.file_complete)

    def do_open(self, args):
        """Opens the given application install.  Optionally, with the given file[s].

        Usage: open [install] [files...]

        install:  The name of the houdini install to open.
        """
        args = self.parse_arguments(args)
        if len(args) < 1:
            self.perror("No install specified.")
            return

        files = args[1:]

        routines = self.get_configuration_routines()
        routines.load()
        asset_path = routines.get_asset_path()

        abs_files = []

        for file in files:
            abs_files.append(os.path.join(asset_path,file))

        man = routines.get_manager()
        install = man.get_by_name(args[0])

        routines.open_application(install, [], abs_files)


