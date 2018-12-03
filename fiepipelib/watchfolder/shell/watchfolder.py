import os
import os.path
import typing

from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.watchfolder.routines.Watcher import WatcherRoutines, start_watching_routine


class WatchFolderShellApplication(AbstractShell):
    _watchers: typing.Dict[str, WatcherRoutines]

    def __init__(self):
        super().__init__()
        self._watchers = {}

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(WatchFolderShellApplication, self).get_plugin_names_v1()
        ret.append("watchfolder_shellapplication")
        return ret

    def get_prompt_text(self) -> str:
        return "watchfolder"

    __icloud_watcher_name = "iCloudDrive"

    def running_watchers_complete(self, text, line, begidx, endidx):
        ret = []
        for wname in self._watchers.keys():
            if wname.lower().startswith(text.lower()):
                ret.append(wname)
        return ret

    complete_stop_watch = running_watchers_complete

    def do_stop_watch(self, args):
        """Stops the given watcher folder

        Usage: stop_watch [name]

        name:  The name of the watch to stop
        """
        args = self.parse_arguments(args)
        name = args[0]

        if len(args) < 1:
            self.perror("No name givne.")
            return

        if name not in self._watchers.keys():
            self.perror("No such watcher.")
            return

        watcher = self._watchers.pop(name)
        watcher.stop_watching()

    def do_list_watches(self, args):
        """Lists the running watchers

        Usage list_watches"""
        args = self.parse_arguments(args)

        for (name, watcher) in self._watchers.items():
            self.poutput(name + " : " + watcher.path)

    def do_start_icloud(self, args):
        """Starts a watchfolder in the user's iCloud directory

        Usage: start_icloud
        """

        if self.__icloud_watcher_name in self._watchers.keys():
            self.perror(self.__icloud_watcher_name + " watcher already running.")
            return

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

        watcher = self.do_coroutine(start_watching_routine(icloud_dir, self.get_feedback_ui()))
        self._watchers[self.__icloud_watcher_name] = watcher

    __documents_watcher_name = "documents"

    def do_start_documents(self, args):
        """Starts a watchfolder in the user's Documents directory

        Usage: start_documents
        """
        args = self.parse_arguments(args)

        if self.__documents_watcher_name in self._watchers.keys():
            self.perror(self.__documents_watcher_name + " watcher already running.")
            return

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

        watcher = self.do_coroutine(start_watching_routine(docs_dir, self.get_feedback_ui()))
        self._watchers[self.__documents_watcher_name] = watcher

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

        for watcher in self._watchers.values():
            if os.path.samefile(watcher.path, path):
                self.perror("Path already being watched.")
                return

        if name in self._watchers.keys():
            self.perror("Name already exists.")
            return

        if not os.path.exists(path):
            self.perror("No such path: " + path)
            return

        if not os.path.isdir(path):
            self.perror("Not a directory: " + path)
            return

        watcher = self.do_coroutine(start_watching_routine(path, self.get_feedback_ui()))
        self._watchers[name] = watcher


def main():
    # p = get_local_platform_routines
    # u = LocalUserRoutines(p)
    s = WatchFolderShellApplication()
    s.cmdloop()


if __name__ == "__main__":
    main()
