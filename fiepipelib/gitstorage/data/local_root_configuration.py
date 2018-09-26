import fiepipelib.components
import fiepipelib.container.local_config.data.localcontainerconfiguration
import fiepipelib.storage.localvolume
import os.path
import fiepipelib.container
import git
import typing
import fiepipelib.gitstorage.data.git_working_asset
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfiguration
from fiepipelib.components.data.components import AbstractNamedItemListComponent
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper
def LocalRootConfigFromJSONData(data):
    ret = LocalRootConfiguration()
    ret._id = data['id']
    ret._volumeName = data['volume_name']
    ret._subPath = data['sub_path']
    return ret

def LocalRootConfigToJSONData(root):
    data = {}
    data['version'] = 1
    data['id'] = root._id
    data['volume_name'] = root._volumeName
    data['sub_path'] = root._subPath
    return data

def LocalRootConfigFromParameters(id, volumeName, subPath):
    ret = LocalRootConfiguration()
    ret._id = id
    ret._volumeName = volumeName
    ret._subPath = subPath
    return ret
    
class LocalRootConfiguration(object):
    """Represents a configured local working directory root."""

    _id = None

    def GetID(self):
        """The ID of the working directory root this configuration is for.
        This should match the ID on the workingdirectoryroot"""
        return self._id

    _volumeName = None
    
    def GetVolumeName(self):
        """The name of the volume on which this working directory resides"""
        return self._volumeName

    _subPath = None

    def GetWorkingSubPath(self):
        """The relative path within the volume, which points to the git working directory/tree.
        """
        return self._subPath

    def GetWorkingPath(self, mapper:localstoragemapper):
        """Returns the absolute path of the working directory root based on the data in
        this object and the passed registry.

        @param localVolumeRegistry: An instance of the localvolumeregistry to use to complete the lookup.
        """
        mountedWorkingVols = mapper.GetMountedWorkingStorage()
        volume = None
        for mountedWorkingVol in mountedWorkingVols:
            if mountedWorkingVol.GetName() == self.GetVolumeName():
                volume = mountedWorkingVol
        if volume == None:
            raise fiepipelib.storage.localvolume.VolumeNotFoundException(self.GetVolumeName())
        assert isinstance(volume, fiepipelib.storage.localvolume.localvolume)
        volPath = volume.GetPath()
        return os.path.join(volPath,self.GetWorkingSubPath())

    def GetRepo(self, mapper:localstoragemapper):
        """Returns a git repository based on the data in this opbject and the passed registry.

        Note: the givne git repo object isn't guaronteed to be pointing to a working repo.

        @param localVolumeRegistry: An instance of the localvolumeregistry to use to complete the lookup.
        """
        return git.Repo(self.GetWorkingPath(mapper))

    def GetWorkingAssets(self, mapper:localstoragemapper, recursive = False) -> typing.List[GitWorkingAsset]:
        """Returns a list of workingasset objects found in this root.
        @param recursive: If False (default) we only get the working assets directly accessible from this root.
        If True, we get the working assets from this root, and those asssets and those assets and so-on.  We do
        not execute further checkouts.  So, if a submodule isn't cloned, it won't be recursed into; though it will
        be included in the list.
        """
        repo = self.GetRepo(mapper)
        assert isinstance(repo, git.Repo)
        ret = []
        for submodule in repo.iter_submodules():
            asset = GitWorkingAsset(submodule)
            ret.append(asset)
        return ret


class LocalRootConfigurationsComponent(AbstractNamedItemListComponent[LocalRootConfiguration]):

    def ItemFromJSONData(self, data:dict) -> LocalRootConfiguration:
        return LocalRootConfigFromJSONData(data)
    
    def ItemToJSONData(self, item:LocalRootConfiguration) -> dict:
        return LocalRootConfigToJSONData(item)

    def item_to_name(self, item: LocalRootConfiguration) -> str:
        return item.GetID()

    def GetComponentName(self):
        return "git_local_working_directory_roots"

    def __init__(self, conf:LocalContainerConfiguration):
        """@param conf: a LocalContainerConfiguration to use to store data.
        """
        super().__init__(conf)

    def get_by_id(self, id:str):
        for item in self.GetItems():
            if item.GetID() == id:
                return item
        raise LookupError()
