import fiepipelib.gitstorage.asset
import git
import fiepipelib.gitstorage.routines.submodules

def CreateNewEmpty(repo, subPath):
    assert isinstance(repo, git.Repo)
    assert isinstance(subPath, str)

class workingasset(object):
    """Represents a copy of an asset on working storage.  Though it may not
    be cloned to disk yet, it has all the data neccesary to be cloned to disk.

    Workingassets are created from git submodules.
    """

    _submodule = None

    def GetSubmodule(self):
        return self._submodule

    def __init__(self, submodule):
        assert isinstance(submodule, git.Submodule )
        self._submodule = submodule
        id = submodule.name
        
    def GetAsset(self):
        id = self._submodule.name
        return fiepipelib.gitstorage.asset.asset(id)

    def GetSubWorkingAssets(self):
        ret = []
        submods = self.GetSubmodule().children()
        for submod in submods:
            assert isinstance(submod, git.Submodule)
            ret.append(workingasset(submod))
        return ret

    def IsCheckedOut(self):
        return self.GetSubmodule().module_exists()
        

