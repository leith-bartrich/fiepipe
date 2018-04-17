import fiepipelib.abstractmanager
import fiepipelib.gitstorage.workingasset
import os.path

class abstractassetlocalmanager(fiepipelib.abstractmanager.abstractmanager):
    """Subclass this.
    
    A local manager than knows how to save its data to sqlite databases in the asset's local fiepipe configuration directory.

    Implements the GetConfigDir abstract method.

    All others must still be overidden from the superclass.
    """

    _workingAsset = None

    def __init__(self, workingAsset):
        assert isinstance(workingAsset, fiepipelib.gitstorage.workingasset.workingasset)
        self._workingAsset = workingAsset
        super().__init__()

    def GetConfigDir(self):
        if not self._workingAsset.IsCheckedOut():
            raise git.GitError("Asset is not checked out.")
        return os.path.join(self._workingAsset.GetSubmodule().abspath,".assetlocal","local_managers")
