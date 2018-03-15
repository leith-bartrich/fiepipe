import fiepipelib.storage.localvolume
import fiepipelib.localuser
import os
import os.path

class localstoragemapper(object):
    """Handles the logic behind mapping requests for storage, to actual local storage.  Mostly used when creating git storge.
    
    Always maps mounted removable storage as available.
    """

    _localUser = None
    _localVolumeRegistry = None

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        self._localUser = localUser
        self._localVolumeRegistry = fiepipelib.storage.localvolume.localvolumeregistry(localUser)

    def GetMountedWorkingStorage(self):
        """Gets the currently mounted volumes marked as suitable for being a working volume."""
        all = fiepipelib.storage.localvolume.GetAllMountedVolumes(self._localUser,[fiepipelib.storage.localvolume.CommonAdjectives.containerrole.WORKING_VOLUME])
        ret = []
        for v in all:
            assert isinstance(v, fiepipelib.storage.localvolume.localvolume)
            if v.HasAdjective(fiepipelib.storage.localvolume.CommonAdjectives.containerrole.WORKING_VOLUME):
                ret.append(v)
        return ret

    def GetMountedWorkingStorageByName(self, name):
        """Raises KeyError if not found
        """
        all = self.GetMountedWorkingStorage()
        for s in all:
            if s.GetName() == name:
                return s
        raise KeyError(name)

    def GetMountedBackingStorage(self):
        """Gets the currently mounted volumes marked as suitable for being a backing volume."""
        all = fiepipelib.storage.localvolume.GetAllMountedVolumes(self._localUser,[fiepipelib.storage.localvolume.CommonAdjectives.containerrole.BACKING_VOLUME])
        ret = []
        for v in all:
            assert isinstance(v, fiepipelib.storage.localvolume.localvolume)
            if v.HasAdjective(fiepipelib.storage.localvolume.CommonAdjectives.containerrole.BACKING_VOLUME):
                ret.append(v)
        return ret

    def GetMountedBackingStorageByName(self, name):
        """Raises KeyError if not found
        """
        all = self.GetMountedBackingStorage()
        for s in all:
            if s.GetName() == name:
                return s
        raise KeyError(name)

    def GetMountedArchivalStorage(self):
        """Gets the currently mounted volumes marked as suitable for being an archival volume."""
        all = fiepipelib.storage.localvolume.GetAllMountedVolumes(self._localUser,[fiepipelib.storage.localvolume.CommonAdjectives.containerrole.ARCHIVE_VOLUME])
        ret = []
        for v in all:
            assert isinstance(v, fiepipelib.storage.localvolume.localvolume)
            if v.HasAdjective(fiepipelib.storage.localvolume.CommonAdjectives.containerrole.ARCHIVE_VOLUME):
                ret.append(v)
        return ret

    def GetMountedArchivalStorageByName(self, name):
        """Raises KeyError if not found
        """
        all = self.GetMountedArchivalStorage()
        for s in all:
            if s.GetName() == name:
                return s
        raise KeyError(name)
