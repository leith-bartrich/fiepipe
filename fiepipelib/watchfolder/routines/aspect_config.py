import pkg_resources
import typing
import time
import datetime
import signal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from threading import Thread
from fiepipelib.assetaspect.routines.config import AssetAspectConfigurationRoutines
from fiepipelib.assetaspect.routines.autoconf import AutoConfigurationResult
from fiepipelib.gitstorage.routines.gitasset import GitAssetInteractiveRoutines
from fiepipelib.watchfolder.data.aspect_config import WatchFolderConfig
from fieui.FeedbackUI import AbstractFeedbackUI


class WatcherRoutines(AssetAspectConfigurationRoutines[WatchFolderConfig]):
    _feedback_ui: AbstractFeedbackUI = None

    _observer: Observer = None

    def __init__(self, config: WatchFolderConfig, asset_routines: GitAssetInteractiveRoutines, feedback_ui: AbstractFeedbackUI):
        self._feedback_ui = feedback_ui
        super().__init__(config, asset_routines)

    def default_configuration(self):
        pass

    async def reconfigure_interactive_routine(self):
        pass

    async def auto_reconfigure_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoConfigurationResult:
        pass

    async def start_watching_routine(self, asset_path: str, watch_dir_path: str):
        self._queue = []
        self._observer = Observer()

        await self._feedback_ui.feedback("Loading plugins...")
        await self._feedback_ui.feedback("asset: " + asset_path)
        await self._feedback_ui.feedback("watch dir: " + watch_dir_path)
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.watchfolder.watch")
        for entrypoint in entrypoints:
            await self._feedback_ui.feedback("plugin: " + entrypoint.name)
            method = entrypoint.load()
            method(self, asset_path, watch_dir_path)
        await self._feedback_ui.feedback("Plugins loaded.")
        await self._feedback_ui.feedback("Starting...")
        self._observer.start()

    def schedule_handler(self, handler: FileSystemEventHandler, path: str, recurse: bool):
        return self._observer.schedule(handler, path, recurse)

    def unschedule_handler(self, observed_watch):
        self._observer.unschedule(observed_watch)

    def stop_watching(self):
        self._queue.clear()
        self._observer.stop()
        self._observer.join()

    _queue:typing.List[typing.Awaitable] = None
    _request_stop = False

    def request_stop_queue(self):
        self._request_stop = True

    def ctrl_c_sig(self, sig, frame):
        self.request_stop_queue()

    def queue_task(self, task:typing.Awaitable):
        self._queue.append(task)

    async def process_queue(self):
        self._request_stop = False
        await self._feedback_ui.output("Beginning queue processing...")
        await self._feedback_ui.output("CTRL C to stop queue.")
        try:
            while not self._request_stop:
                while len(self._queue) != 0:
                    if self._request_stop:
                        break
                    now = datetime.datetime.now()
                    await self._feedback_ui.output("Found task: " + now.strftime("%Y-%m-%d %H:%M:%S.%F %z"))
                    task_thread = self._queue.pop(0)
                    await task_thread()
                    await self._feedback_ui.output("CTRL C to stop queue.")
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
        await self._feedback_ui.output("Ending queue processing.")

    @property
    def feedback_ui(self):
        return self._feedback_ui


