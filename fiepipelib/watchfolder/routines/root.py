import pkg_resources
import asyncio

from watchdog.observers import Observer

from fiepipelib.watchfolder.data.root import RootDirEventHandler
from fieui.FeedbackUI import AbstractFeedbackUI


class WatcherRoutines(object):
    _feedback_ui: AbstractFeedbackUI = None

    _path: str = None
    _observer: Observer = None
    _root_handler: RootDirEventHandler = None

    def __init__(self, path: str, feedback_ui: AbstractFeedbackUI):
        self._path = path
        self._feedback_ui = feedback_ui

    async def start_watching_routine(self):
        self._observer = Observer()
        self._root_handler = RootDirEventHandler()
        await self._feedback_ui.feedback("Watch root path: " + self._path)
        self._observer.schedule(self._root_handler, self._path, False)

        await self._feedback_ui.feedback("Loading plugins...")
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.watchfolder.watch")
        for entrypoint in entrypoints:
            await self._feedback_ui.feedback("plugin: " + entrypoint.name)
            method = entrypoint.load()
            handler, sub_path, recurse = method()
            watch_path = os.path.join(self._path, sub_path)
            await self._feedback_ui.feedback("plugin: " + entrypoint.name + " path: " + watch_path)
            self._observer.schedule(handler, watch_path, recurse)
        await self._feedback_ui.feedback("Plugins loaded.")
        await self._feedback_ui.feedback("Starting...")
        self._observer.start()

    def stop_watching(self):
        self._observer.stop()
        self._observer.join()

    @property
    def path(self):
        return self._path


async def start_watching_routine(path: str, feedback_ui: AbstractFeedbackUI) -> WatcherRoutines:
    ret = WatcherRoutines(path, feedback_ui)
    await ret.start_watching_routine()
    return ret
