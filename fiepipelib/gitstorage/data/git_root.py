import os
import os.path
import uuid

import git

import fiepipelib.components
import fiepipelib.container
import fiepipelib.gitstorage.data.localstoragemapper
import fiepipelib.storage.localvolume
from fiepipelib.components.data.components import AbstractNamedItemListComponent
from fiepipelib.container.shared.data.container import Container
from fiepipelib.git.routines.repo import InitBareRepository


def RootFromJSONData(data):
    ret = GitRoot()
    ret._id = data['id']
    ret._description = data['description']
    ret._name = data['name']
    return ret


def RootToJSONData(r):
    assert isinstance(r, GitRoot)
    ret = {}
    ret['version'] = 1
    ret['id'] = r._id
    ret['description'] = r._description
    ret['name'] = r._name
    return ret


def RootFromParameters(id, name, description):
    ret = GitRoot()
    ret._id = id
    ret._description = description
    ret._name = name
    return ret


def GenerateNewID():
    u = uuid.uuid4()
    return str(u)


class GitRoot(object):
    """A git working directory root.
    
    Such a root represents a root level working directory backed by git storage, within a container.

    The existance of a root in the container provides enough data to hopefully resolve more useful and practical things.  Such as:

    -An actual git working directory on the local system. (but you'll need a local configuration for that)
    -An actual git backing store on a removable volume. (but you'll need a local configuration for that)
    -An actual git backing store on the network. (but you'll need a state server for that)
    -An actual git archive. (but you'll need a state server for that)
    -etc (open ended system)
    """

    _id = None

    def GetID(self):
        """Returns a text string that is a unique ID for this root.
        Usually it's a text representation of a UUID.  In this way, we can
        manage the difference between two different roots being named the same.
        Which is a likely scenario becasue people often re-use names without understanding
        the full history of things.
        """
        return self._id

    _description = None

    def GetDescription(self):
        """A short description of the purpose of understanding this root."""
        return self._description

    _name = None

    def GetName(self):
        """Returns a short simple name to use in identifying this root.
        Ideally the name will be used to name a directory on disk.  Although
        the local user can override this behavior.  None the less, it should be
        one word, lower-cass and have no white-space, in order to maintain maximum
        compatibility.

        Since the fiepipe system will usually use the ID to keep track of these, two different
        roots with the same name can exist either at the same time, or at different times.  Though
        this might be confusing and should be avoided if possible.
        """
        return self._name

    def FindOnMountedBackingVolumes(self, localstoragemapper):
        """Finds any git repositories on mounted backing storage that is for this asset.
        The path can be found by passing the returned volumes to GetPathForBackingVolume.

        In the case that the asset is backed on more than one mounted volume, they are all returned.
        Disambiguation is to be handled by the calling routine, logic or user.

        @return: The mounted volumes on which this asset's backing can be found."""
        assert isinstance(localstoragemapper, fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper)
        volumes = localstoragemapper.GetMountedBackingStorage()
        ret = []
        for volume in volumes:
            if (os.path.exists(self.GetPathForBackingVolume(volume))):
                ret.append(volume)
        return ret

    def FindOnMountedArchiveVolumes(self, localstoragemapper):
        """Finds any git repositories on mounted backing storage that is for this asset.
        The path can be found by passing the returned volumes to GetPathForBackingVolume.

        In the case that the asset is backed on more than one mounted volume, they are all returned.
        Disambiguation is to be handled by the calling routine, logic or user.

        @return: The mounted volumes on which this asset's backing can be found."""
        assert isinstance(localstoragemapper, fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper)
        volumes = localstoragemapper.GetMountedArchivalStorage()
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
        fiepipedir = os.path.join(vol.GetPath(), "fiepipe")
        assetsdir = os.path.join(fiepipedir, "git_roots_backing")
        assetdir = os.path.join(assetsdir, self._id + ".git")
        return assetdir

    def GetPathForArchiveVolume(self, vol):
        """Returns the path for this asset as it should be on an archive volume.
        One can use this to create a repository.  Or, 
        a git Repo can be constructed from this using git.Repo(path)
        for example."""
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        fiepipedir = os.path.join(vol.GetPath(), "fiepipe")
        assetsdir = os.path.join(fiepipedir, "git_roots_archive")
        assetdir = os.path.join(assetsdir, self._id + ".git")
        return assetdir

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

    def CreateRepositoryOnBackingVolume(self, vol):
        """Creates an empty bare repository on the given volume, for this GitRoot.
        @return: the new repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForBackingVolume(vol)
        return InitBareRepository(assetdir)

    def CreateRepositoryOnArchiveVolume(self, vol):
        """Creates an empty bare repository on the given volume, for this GitRoot.
        @return: the new repository
        """
        assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
        assetdir = self.GetPathForArchiveVolume(vol)
        return InitBareRepository(assetdir)


class SharedGitRootsComponent(AbstractNamedItemListComponent[GitRoot]):
    """Component for managing GIT working directory roots within this container."""

    def __init__(self, cont: Container):
        assert isinstance(cont, Container)
        super().__init__(cont)

    def item_to_name(self, item: GitRoot) -> str:
        return item.GetName()

    def ItemToJSONData(self, item: GitRoot):
        return RootToJSONData(item)

    def ItemFromJSONData(self, data: dict) -> GitRoot:
        return RootFromJSONData(data)

    def GetComponentName(self):
        return "git_working_directory_roots"

    def get_by_id(self, id: str):
        for item in self.GetItems():
            if item.GetID() == id:
                return item
        raise LookupError("no such id: " + id)
