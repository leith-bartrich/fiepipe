import uuid
import fiepipelib.gitstorage.data.localstoragemapper
import fiepipelib.storage.localvolume
import os.path
import git

def NewID():
    return str(uuid.uuid4())

class GitAsset(object):
    """An high level, almost abstract representation of a git backed directory that in turn, represents a logical asset.
    
    This object only represents the asset's existence.  Think of it as an abstract handle.

    It is constructed only from an id.  Which may be the only thing you know about an asset at some points in time.

    An asset ID might be obtained from:

    -Network Storage.
    -Archival Storage.
    -Another asset which uses this asset as a submodule.
    """

    _id = None

    def GetID(self):
        """The ID that is used to track this asset across storage.
        """
        return self._id

    def __init__(self, id):
        """@param id: String representation of the ID which must be a UUID.
        """
        u = uuid.UUID(id)
        self._id = str(id)

    def FindOnMountedBackingVolumes(self, mapper):
        """Finds any mounted backing volumes for which git repositories exist for this asset.
        The path or repo can be retrieved by passing the returned volumes to
        GetPathForBackingVolume or GetRepoForBackingVolume.

        In the case that the asset is backed on more than one mounted volume, they are all returned.
        Disambiguation is to be handled by the calling routine, logic or user.

        @return: The mounted volumes on which this asset's backing can be found."""
        assert isinstance(mapper, fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper)
        volumes = mapper.GetMountedBackingStorage()
        ret = []
        for volume in volumes:
            if (os.path.exists(self.GetPathForBackingVolume(volume))):
                ret.append(volume)
        return ret

    def FindOnMountedArchiveVolumes(self, mapper):
        """Finds any mounted archive volumes for which git repositories exist for this asset.
        The path or repo can be retrieved by passing the returned volumes to
        GetPathForArchiveVolume or GetRepoForArchiveVolume.

        In the case that the asset is backed on more than one mounted volume, they are all returned.
        Disambiguation is to be handled by the calling routine, logic or user.

        @return: The mounted volumes on which this asset's backing can be found."""
        assert isinstance(mapper, fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper)
        volumes = mapper.GetMountedArchivalStorage()
        ret = []
        for volume in volumes:
            if (os.path.exists(self.GetPathForArchiveVolume(volume))):
                ret.append(volume)
        return ret


    def GetPathForBackingVolume(self, vol):
        """Returns the path for this asset as it should be on a backing volume.
        One can use this to create a repository.  Or, 
        a git Repo can be constructed from this using git.Repo(path)
        for example."""
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        fiepipedir = os.path.join(volume.GetPath(),"fiepipe")
        assetsdir = os.path.join(fiepipedir,"git_assets_backing")
        assetdir = os.path.join(assetsdir,self._id + ".git")
        return assetdir

    def GetPathForArchiveVolume(self, vol):
        """Returns the path for this asset as it should be on a archive volume.
        One can use this to create a repository.  Or, 
        a git Repo can be constructed from this using git.Repo(path)
        for example."""
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        fiepipedir = os.path.join(volume.GetPath(),"fiepipe")
        assetsdir = os.path.join(fiepipedir,"git_assets_archive")
        assetdir = os.path.join(assetsdir,self._id + ".git")
        return assetdir


    def CreateRepositoryOnBackingVolume(self, vol):
        """Creates an empty bare repository on the given volume, for this asset.
        @return: the new repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForBackingVolume(vol)
        return fiepipelib.gitstorage.routines.repo.InitBareRepository(assetdir)

    def CreateRepositoryOnArchiveVolume(self, vol):
        """Creates an empty bare repository on the given volume, for this asset.
        @return: the new repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForArchiveVolume(vol)
        return fiepipelib.gitstorage.routines.repo.InitBareRepository(assetdir)

    def GetRepositoryOnArchiveVolume(self, vol, create=False):
        """Checks for and creates an empty bare repository on the given volume, for this asset
        if neccesary.

        @return: the repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForArchiveVolume(vol)
        if not fiepipelib.gitstorage.routines.repo.RepoExists(assetdir):
            if create:
                fiepipelib.gitstorage.routines.repo.InitBareRepository(assetdir)         
            else:
                raise fiepipelib.gitstorage.routines.repo.NoSuchRepoError()
        return git.Repo(assetdir)

    def GetRepositoryOnBackingVolume(self, vol, create=False):
        """Checks for and creates an empty bare repository on the given volume, for this asset
        if neccesary.

        @return: the repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForBackingVolume(vol)
        if not fiepipelib.gitstorage.routines.repo.RepoExists(assetdir):
            if create:
                fiepipelib.gitstorage.routines.repo.InitBareRepository(assetdir)         
            else:
                raise fiepipelib.gitstorage.routines.repo.NoSuchRepoError()
        return git.Repo(assetdir)
