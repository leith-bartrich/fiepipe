import git
import os.path
import pathlib
import fiepipelib.gitstorage.localstoragemapper
import fiepipelib.gitstorage.root
import fiepipelib.gitstorage.workingroot
import fiepipelib.storage.localvolume
import fiepipelib.gitstorage.routines.workingdirectoryasset
import fiepipelib.gitstorage.routines.repo


def IsFullyCheckedOut(workingRoot, localUser):
    """Returns true if the root is fully checked out. Meaning all assets and subassets are checked out.
    """
    assert isinstance(workingRoot, fiepipelib.gitstorage.localworkingdirectoryroot.workingroot)
    assert isinstance(localUser, fiepipelib.localuser.localuser)
    mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(localUser)

    for subWorkingAsset in workingRoot.GetWorkingAssets(mapper,False):
        if not fiepipelib.gitstorage.routines.workingdirectoryasset.IsFullyCheckedOut(subWorkingAsset):
            return False

def PushRootToArchive(root, workingRoot, archiveVolume, localUser):
    """Pushes the given root to the given archive volume.  Creates it if neccesary.

    This is not recursive with regard to assets or submodules.
    """
    assert isinstance(root, fiepipelib.gitstorage.root.root)
    assert isinstance(workingRoot, fiepipelib.gitstorage.workingroot.workingroot)
    assert isinstance(localUser, fiepipelib.localuser.localuser)
    mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(localUser)

    workingRepo = workingRoot.GetRepo(mapper)
    archiveRepoPath = root.GetPathForArchiveVolume(archiveVolume)
    
    root.GetRepositoryOnArchiveVolume(archiveVolume,create=True)

    remote = workingRepo.create_remote(archiveVolume.GetName(),archiveRepoPath)
    print("Pushing root to: " + archiveRepoPath)
    remote.push("master")
    workingRepo.delete_remote(remote.name)

def PushRootToArchiveRecursive(root, workingRoot, archiveVolume, localUser):
    """Pushes the given root to the given archive volume.  Creates it if neccesary.

    Recurses into assets

    Skips assets that are not checked out (are not local)
    """

    assert isinstance(root, fiepipelib.gitstorage.root.root)
    assert isinstance(workingRoot, fiepipelib.gitstorage.workingroot.workingroot)
    assert isinstance(localUser, fiepipelib.localuser.localuser)

    PushRootToArchive(root,workingRoot,archiveVolume,localUser)

    for subWorkingAsset in workingRoot.GetWorkingAssets(mapper,False):
        print("Moving into Sub-Asset: " + subWorkingAsset.GetSubmodule().abspath)
        if subWorkingAsset.IsCheckedOut():
            fiepipelib.gitstorage.routines.workingdirectoryasset.PushToArchiveVolumeRecursive(subWorkingAsset.GetAsset(),archiveVolume,localUser)
        else:
            print("Sub-Asset not checked out.  Skipping.")





