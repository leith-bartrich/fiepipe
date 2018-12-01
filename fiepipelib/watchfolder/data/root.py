from watchdog.events import FileSystemEventHandler


class RootDirEventHandler(FileSystemEventHandler):
    """Currently, the root directory doesn't do anything.  But we watch anyway.
    """

    def on_any_event(self, event):
        super().on_any_event(event)

    def on_moved(self, event):
        super().on_moved(event)

    def on_created(self, event):
        super().on_created(event)

    def on_deleted(self, event):
        super().on_deleted(event)

    def on_modified(self, event):
        super().on_modified(event)
