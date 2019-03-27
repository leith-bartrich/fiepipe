import fiepipelib.gitstorage.data.git_asset
import git
import fiepipelib.git.routines.submodules

def CreateNewEmpty(repo, subPath):
    assert isinstance(repo, git.Repo)
    assert isinstance(subPath, str)

class GitWorkingAsset(object):
    """Represents a copy of an asset on working storage.  Though it may not
    be cloned to disk yet, it has all the data neccesary to be cloned to disk.

    Workingassets are created from git submodules.
    """

    _submodule = None

    def GetSubmodule(self) -> git.Submodule:
        return self._submodule

    def GetRepo(self) -> git.Repo:
        submod = self.GetSubmodule()
        return submod.module()

    def __init__(self, submodule):
        assert isinstance(submodule, git.Submodule )
        self._submodule = submodule
        id = submodule.name
        
    def GetAsset(self):
        id = self._submodule.name
        return fiepipelib.gitstorage.data.git_asset.GitAsset(id)

    def GetSubWorkingAssets(self):
        ret = []
        repo = self.GetRepo()
        for submod in repo.submodules:
            assert isinstance(submod, git.Submodule)
            ret.append(GitWorkingAsset(submod))
        return ret

    def IsCheckedOut(self):
        return self.GetSubmodule().module_exists()
        

