import os
import os.path

import pkg_resources
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from fieui.FeedbackUI import AbstractFeedbackUI


class WatcherRoutines(object):
    _feedback_ui: AbstractFeedbackUI = None

    _path: str = None
    _observer: Observer = None

    def __init__(self, path: str, feedback_ui: AbstractFeedbackUI):
        self._path = path
        self._feedback_ui = feedback_ui

    async def start_watching_routine(self):
        self._observer = Observer()

        await self._feedback_ui.feedback("Loading plugins...")
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.watchfolder.watch")
        for entrypoint in entrypoints:
            await self._feedback_ui.feedback("plugin: " + entrypoint.name)
            method = entrypoint.load()
            method(self)
        await self._feedback_ui.feedback("Plugins loaded.")
        await self._feedback_ui.feedback("Starting...")
        self._observer.start()

    def schedule_handler(self, handler: FileSystemEventHandler, subpath: str, recurse: bool):
        watch_path = os.path.join(self._path, subpath)
        return self._observer.schedule(handler, watch_path, recurse)

    def unschedule_handler(self, observed_watch):
        self._observer.unschedule(observed_watch)

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
