import git
import fiepipelib.gitstorage.data.localstoragemapper
import fiepipelib.gitstorage.workingdirectoryroot
import fiepipelib.gitstorage.localworkingdirectoryroot
import fiepipelib.storage.localvolume

class AssetNotCheckedOutError(git.GitError):
    pass

def IsFullyCheckedOut(workingAsset):
    """Indicates if an assets sub-assets are all checked out recursively.
    """
    assert isinstance(workingAsset, fiepipelib.gitstorage.workingasset.workingasset)
    if workingAsset.IsCheckedOut():
        subWorkingAssets = workingAsset.GetSubWorkingAssets()
        for subWorkingAsset in subWorkingAssets:
            if not IsFullyCheckedOut(subWorkingAsset):
                return False
    else:
        return False

def WalkAssetsAndCallback(workingAsset, callback, recursive = True):
    """Recruse from a workingAsset through its submodule workingAssets as per passed rules.
    
    callback(workingAsset) - called upon recursing into a valid workingAsset that is checked out.

    notCheckedOutCallback(workingAsset) - called upon recursing into a valid workingAsset that is not checked out.

    If recursive, will descend.
    """
    assert isinstance(workingAsset, fiepipelib.gitstorage.workingasset.workingasset)
    
    callback(workingAsset)
    if recursive:
        subWorkingAssets = workingAsset.GetSubWorkingAssets()
        for subWorkingAsset in subWorkingAssets:
            WalkAssetsAndCallback(subWorkingAsset,callback,recursive)

def PushToArchiveVolume(workingAsset, archiveVol, localUser):
    """Pushes the working asset to the given archiveVolume, creating the repository if it doesn't exist.
    """

    assert isinstance(workingAsset, fiepipelib.gitstorage.workingasset.workingasset)
    assert isinstance(archiveVol, fiepipelib.storage.localvolume.localvolume)
    assert isinstance(localUser,fiepipelib.localuser.localuser)
    mapper = fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper(localUser)
    wRepo = workingAsset.GetSubmodule().module()
    assert isinstance(wRepo, git.Repo)

    workingAsset.GetAsset().GetRepositoryOnArchiveVolume(archiveVol,True)
    archiveRepoPath = workingAsset.GetAsset().GetPathForArchiveVolume(archiveVol)
    
    #guaronteed it exists, and we have its path

    remote = wRepo.create_remote(archiveVol.GetName(),archiveRepoPath)
    workingTreeDir = wRepo.working_tree_dir()
    print("Pushing asset " + workingTreeDir + " to: " + archiveRepoPath)
    remote.push_routine()
    wRepo.delete_remote(remote.name)


def PushToArchiveVolumeRecursive(workingAsset, archiveVol, localUser, recursive = True):
    """Pushes the given local working asset to the given backing volume.
    Creates the repository if they don't exist.

    if recursive, walks sub assets recursively.

    Warns if an asset is not checked out.
    Warns if the volume isn't mounted.
    """
    assert isinstance(workingAsset, fiepipelib.gitstorage.workingasset.workingasset)
    assert isinstance(archiveVol, fiepipelib.storage.localvolume.localvolume)
    assert isinstance(localUser,fiepipelib.localuser.localuser)
    mapper = fiepipelib.gitstorage.data.localstoragemapper.localstoragemapper(localUser)

    asset = workingAsset.GetAsset()

    #check mounted
    if not archiveVol.IsMounted():
        print("Backing volume not mounted.")
        return

    def callback(wAss):
        assert isinstance(wAss, fiepipelib.gitstorage.workingasset.workingasset)
        if wAss.IsCheckedOut():
            PushToArchiveVolume(wAss,archiveVol,localUser)
        else:
            print("Asset not checked out: " + wAss.GetSubmodule().abspath)
            print ("Skipping.")
            
    WalkAssetsAndCallback(workingAsset,callback,recursive)


    
    

