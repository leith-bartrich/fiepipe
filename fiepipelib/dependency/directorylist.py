import watchdog
import watchdog.events
import watchdog.observers
import os.path

class handler(watchdog.events.FileSystemEventHandler):

    _dirList = None

    def __init__(self, dirlist):
        assert isinstance(dirlist, directorylist)
        self._dirList = directorylist

    def on_created(self, event):
        for h in self._dirList._createdHandlers:
            h(event.src_path,event.is_directory,_dirList)

    def on_deleted(self, event):
        for h in self._dirList._deletedHandlers:
            h(event.src_path,event.is_directory,_dirList)

    def on_modified(self, event):
        for h in self._dirList._modifiedHandlers:
            h(event.src_path,event.is_directory,_dirList)

    def on_moved(self, event):
        for h in self._dirList._modifiedHandlers:
            h(event.src_path,event.dest_path,event.is_directory,_dirList)


class directorylist(object):
    """description of class"""

    _observer = None
    _handler = None

    def __init__(self,path,parent, createdHandlers = [], deletedHandlers = [], modifiedHandlers = [], movedHandlers = []):
        self._observer = watchdog.observers.Observer()
        self._handler = handler(self)
        self._observer.schedule(self._handler,path,False)

        self._createdHandlers = createdHandlers
        self._deletedHandlers = deletedHandlers
        self._modifiedHandlers = modifiedHandlers
        self._movedHandlers = movedHandlers

        self._observer.start()
        for f in os.listdir(path):
            for h in self._createdHandlers:
                p = os.path.join(path,f)
                d = os.path.isdir(p)
                h(p,d,self)



    _createdHandlers = None
    _deletedHandlers = None
    _modifiedHandlers = None
    _movedHandlers = None

    def Register(self, createdHandler, deletedHandler, modifiedHandler, movedHandler):
        """
        Created(path,isDirectory,dirlist)
        Deleted(path,isDirectory,dirlist)
        Modified(path,isDirectory,dirlist)
        Moved(src_path,dest_path,isDirectory,dirlist)
        """
        self._createdHandlers.append(createdHandler)
        self._deletedHandlers.append(deletedHandler)
        self._modifiedHandlers.append(modifiedHandler)
        self._movedHandlers.append(movedHandler)

    def UnRegister(self, createdHandler, deletedHandler, modifiedHandler, movedHandler):
        self._createdHandlers.remove(createdHandler)
        self._deletedHandlers.remove(deletedHandler)
        self._modifiedHandlers.remove(modifiedHandler)
        self._movedHandlers.remove(movedHandler)
