import os
import os.path
import typing

from fiepipelib.assetaspect.shell.config import AssetConfigCommand
from fiepipelib.gitstorage.shells.gitasset import Shell as GitAssetShell
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.watchfolder.data.aspect_config import WatchFolderConfig
from fiepipelib.watchfolder.routines.aspect_config import WatcherRoutines


class WatchFolderShellApplication(AssetConfigCommand[WatchFolderConfig]):

    def __init__(self, asset_shell: GitAssetShell):
        self._watchers = {}
        super().__init__(asset_shell)

    def get_configuration_data(self) -> WatchFolderConfig:
        asset_routines = self.get_asset_shell().get_routines()
        asset_routines.load()
        asset_path = asset_routines.abs_path
        return WatchFolderConfig(asset_path)

    def get_configuration_routines(self) -> WatcherRoutines:
        return WatcherRoutines(self.get_configuration_data(), self.get_asset_shell().get_routines(),
                               self.get_feedback_ui())

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(WatchFolderShellApplication, self).get_plugin_names_v1()
        ret.append("watchfolder.command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self.get_asset_shell().get_prompt_text(), "watchfolder"])

    __icloud_watcher_name = "iCloudDrive"


    def do_start_icloud(self, args):
        """Starts a watchfolder in the user's iCloud directory

        Usage: start_icloud
        """


        args = self.parse_arguments(args)

        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)

        home_dir = user.get_home_dir()

        icloud_dir = os.path.join(home_dir, "iCloudDrive", "fiepipe_watch")

        if not os.path.exists(icloud_dir):
            self.perror("No such path: " + icloud_dir)
            return

        if not os.path.isdir(icloud_dir):
            self.perror("Not a directory: " + icloud_dir)
            return

        routines = self.get_configuration_routines()
        routines.load()
        asset_routines = self.get_asset_shell().get_routines()
        asset_routines.load()

        watchfolder_routines = WatcherRoutines(routines.get_configuration(), asset_routines, self.get_feedback_ui())
        self.do_coroutine(watchfolder_routines.start_watching_routine(asset_routines.abs_path, icloud_dir))
        self.do_coroutine(watchfolder_routines.process_queue())


    __documents_watcher_name = "documents"

    def do_start_documents(self, args):
        """Starts a watchfolder in the user's Documents directory

        Usage: start_documents
        """
        args = self.parse_arguments(args)

        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)

        home_dir = user.get_home_dir()

        docs_dir = os.path.join(home_dir, "Documents", "fiepipe_watch")

        if not os.path.exists(docs_dir):
            self.perror("No such path: " + docs_dir)
            return

        if not os.path.isdir(docs_dir):
            self.perror("Not a directory: " + docs_dir)
            return

        routines = self.get_configuration_routines()
        routines.load()
        asset_routines = self.get_asset_shell().get_routines()
        asset_routines.load()

        watchfolder_routines = WatcherRoutines(routines.get_configuration(), asset_routines, self.get_feedback_ui())
        self.do_coroutine(watchfolder_routines.start_watching_routine(asset_routines.abs_path, docs_dir))
        self.do_coroutine(watchfolder_routines.process_queue())

    def do_start(self, args):
        """Starts a named watchfolder in a given directory

        Usage: start [name] [path]

        name:  the name of the watcher
        path:  the path to the watch directory.
        """
        args = self.parse_arguments(args)

        if len(args) < 1:
            self.perror("No name given.")
            return
        if len(args) < 2:
            self.perror("No path given.")
            return

        name = args[0]
        path = args[1]


        if name in self._watchers.keys():
            self.perror("Name already exists.")
            return

        if not os.path.exists(path):
            self.perror("No such path: " + path)
            return

        if not os.path.isdir(path):
            self.perror("Not a directory: " + path)
            return

        routines = self.get_configuration_routines()
        routines.load()
        asset_routines = self.get_asset_shell().get_routines()
        asset_routines.load()
        watchfolder_routines = WatcherRoutines(routines.get_configuration(), asset_routines, self.get_feedback_ui())
        self.do_coroutine(watchfolder_routines.start_watching_routine(asset_routines.abs_path, path))
        self.do_coroutine(watchfolder_routines.process_queue())


def git_asset_shell_plugin(shell: GitAssetShell):
    command = WatchFolderShellApplication(shell)
    shell.add_submenu(command, "watchfolder", [])
