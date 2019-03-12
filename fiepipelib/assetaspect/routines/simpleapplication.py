import abc
import os
import os.path
import typing

from fiepipelib.applauncher.genericlauncher import listlauncher
from fiepipelib.assetaspect.data.simpleapplication import AbstractSimpleApplicationInstall, \
    AbstractSimpleApplicationInstallsManager
from fiepipelib.assetaspect.routines.config import AssetAspectConfigurationRoutines
from fiepipelib.git.routines.lfs import InstallLFSRepo, Track
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines
from fiepipelib.ui.abspath_input_ui import AbstractAbspathDefaultInputUI
from fieui.FeedbackUI import AbstractFeedbackUI

T = typing.TypeVar("T", bound=AbstractSimpleApplicationInstall)


class AbstractSimpleApplicationInstallInteractiveRoutines(AbstractLocalManagedInteractiveRoutines[T]):
    _path_input_ui: AbstractAbspathDefaultInputUI = None

    def __init__(self, feedback_ui: AbstractFeedbackUI, path_input_ui: AbstractAbspathDefaultInputUI):
        self._path_input_ui = path_input_ui
        super().__init__(feedback_ui)

    @abc.abstractmethod
    def GetManager(self) -> AbstractSimpleApplicationInstallsManager[T]:
        raise NotImplementedError()

    def GetAllItems(self) -> typing.List[T]:
        man = self.GetManager()
        return man.GetAll()

    def ItemToName(self, item: T) -> str:
        return item.get_name()

    def GetItemByName(self, name: str) -> T:
        man = self.GetManager()
        return man.get_by_name(name)

    async def DeleteRoutine(self, name: str):
        man = self.GetManager()
        man.delete_by_name(name)

    async def CreateUpdateRoutine(self, name: str):
        man = self.GetManager()
        try:
            item = man.get_by_name(name)
        except LookupError:
            item = man.FromParameters(name, ".")
        is_valid = False
        path = item.get_path()
        while not is_valid:
            await self.get_feedback_ui().output(item.path_instructions())
            path = await self._path_input_ui.execute("Path to " + man.get_application_name(), item.get_path())
            is_valid, reason = item.validate(path)
            if not is_valid:
                await self.get_feedback_ui().warn("Path invalid: " + reason)

        item._path = path
        man.Set([item])


class AbstractSimpleFiletypeAspectConfigurationRoutines(AssetAspectConfigurationRoutines[T]):



    @abc.abstractmethod
    def get_filetype_extensions(self) -> typing.List[str]:
        """Returns a list of the file extensions this simple application can open.
        e.g. ['exr','png']"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_manager(self) -> AbstractSimpleApplicationInstallsManager:
        raise NotImplementedError()

    def get_installs(self) -> typing.List[AbstractSimpleApplicationInstall]:
        man = self.get_manager()
        return man.GetAll()

    def add_to_git_tracking(self, file_path: str):
        repo = self.get_asset_repo()
        repo.git.add(file_path)

    def get_file_paths(self):
        ret = []
        filetype_extensions = self.get_filetype_extensions()
        for dirname, subdirs, files in os.walk(self.get_asset_path()):
            for file in files:
                base, ext = os.path.splitext(file)
                stripped_ext = ext.lstrip('.')
                for filetype_ext in filetype_extensions:
                    if stripped_ext.lower() == filetype_ext.lower():
                        ret.append(os.path.join(dirname, file))
        return ret

    @abc.abstractmethod
    def get_executable_path(self, install: T) -> str:
        """Returns the executable path to use to open the application."""
        raise NotImplementedError()

    def open_application(self, install: T, args: typing.List[str], files: typing.List[str]):
        launch_args = []
        exec_path = self.get_executable_path(install)
        launch_args.append(exec_path)
        launch_args.extend(args)
        launch_args.extend(files)
        launcher = listlauncher(launch_args)
        launcher.launch()
