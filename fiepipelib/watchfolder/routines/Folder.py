import abc
import os

from watchdog.events import FileSystemEventHandler, FileMovedEvent, DirMovedEvent, FileCreatedEvent, DirCreatedEvent, \
    DirDeletedEvent, FileDeletedEvent, FileModifiedEvent, DirModifiedEvent

from fiepipelib.watchfolder.routines.Watcher import WatcherRoutines


class FolderRoutines(FileSystemEventHandler, abc.ABC):

    _watcher: WatcherRoutines = None
    _subpath: str = None
    _observed_watch = None

    @property
    def subpath(self):
        return self._subpath

    @property
    def watcher(self):
        return self._watcher

    def __init__(self, watcher: WatcherRoutines, subpath: str):
        self._watcher = watcher
        self._subpath = subpath

        dir_path = os.path.join(watcher.path,subpath)
        os.makedirs(dir_path,exist_ok=True)

        self._observed_watch = self._watcher.schedule_handler(self, subpath, False)
        self.emit_existing_events()
        self.on_after_scheduled()

    def on_after_scheduled(self):
        pass

    def stop(self):
        self.watcher.unschedule_handler(self._observed_watch)

    def emit_existing_events(self):
        path = os.path.join(self.watcher.path, self.subpath)
        contents = os.listdir(path)
        for content in contents:
            p = os.path.join(path, content)
            if os.path.isdir(p):
                self.on_existing_dir(p)
            else:
                self.on_existing_file(p)

    @abc.abstractmethod
    def on_existing_file(self, path: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_existing_dir(self, path: str):
        raise NotImplementedError()

    def on_moved(self, event):
        if isinstance(event, FileMovedEvent):
            self.on_file_moved(event)
        elif isinstance(event, DirMovedEvent):
            self.on_dir_moved(event)
        else:
            raise AssertionError

    @abc.abstractmethod
    def on_file_moved(self, event: FileMovedEvent):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_dir_moved(self, event: DirMovedEvent):
        raise NotImplementedError()

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            self.on_file_created(event)
        elif isinstance(event, DirCreatedEvent):
            self.on_dir_created(event)
        else:
            raise AssertionError

    @abc.abstractmethod
    def on_file_created(self, event: FileCreatedEvent):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_dir_created(self, event: DirCreatedEvent):
        raise NotImplementedError()

    def on_deleted(self, event):
        if isinstance(event, FileDeletedEvent):
            self.on_file_deleted(event)
        elif isinstance(event, DirDeletedEvent):
            self.on_dir_deleted(event)
        else:
            raise AssertionError

    @abc.abstractmethod
    def on_file_deleted(self, event: FileDeletedEvent):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_dir_deleted(self, event: DirDeletedEvent):
        raise NotImplementedError()

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            self.on_file_modified(event)
        elif isinstance(event, DirModifiedEvent):
            self.on_dir_modified(event)
        else:
            raise AssertionError

    @abc.abstractmethod
    def on_file_modified(self, event: FileModifiedEvent):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_dir_modified(self, event: DirModifiedEvent):
        raise NotImplementedError()


class RootRoutines(FolderRoutines):
    """Currently, the root directory doesn't do anything.  But we watch anyway.
    """

    def on_file_moved(self, event: FileMovedEvent):
        pass

    def on_dir_moved(self, event: DirMovedEvent):
        pass

    def on_file_created(self, event: FileCreatedEvent):
        pass

    def on_dir_created(self, event: DirCreatedEvent):
        pass

    def on_file_deleted(self, event: FileDeletedEvent):
        pass

    def on_dir_deleted(self, event: DirDeletedEvent):
        pass

    def on_file_modified(self, event: FileModifiedEvent):
        pass

    def on_dir_modified(self, event: DirModifiedEvent):
        pass

    def on_existing_file(self, path: str):
        pass

    def on_existing_dir(self, path: str):
        pass
