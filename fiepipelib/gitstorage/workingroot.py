import fiepipelib.storage.localvolume
import os.path
import fiepipelib.container
import git
import fiepipelib.gitstorage.workingasset 

def RootFromJSONData(data):
    ret = workingroot()
    ret._id = data['id']
    ret._volumeName = data['volume_name']
    ret._subPath = data['sub_path']
    return ret

def RootToJSONData(root):
    data = {}
    data['version'] = 1
    data['id'] = root._id
    data['volume_name'] = root._volumeName
    data['sub_path'] = root._subPath
    return data

def RootFromParameters(id, volumeName, subPath):
    ret = workingroot()
    ret._id = id
    ret._volumeName = volumeName
    ret._subPath = subPath
    return ret
    
class workingroot(object):
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

    def GetWorkingPath(self, mapper):
        """Returns the absolute path of the working directory root based on the data in
        this object and the passed registry.

        @param localVolumeRegistry: An instance of the localvolumeregistry to use to complete the lookup.
        """
        assert isinstance(mapper, fiepipelib.gitstorage.localstoragemapper.localstoragemapper)
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

    def GetRepo(self, mapper):
        """Returns a git repository based on the data in this opbject and the passed registry.

        Note: the givne git repo object isn't guaronteed to be pointing to a working repo.

        @param localVolumeRegistry: An instance of the localvolumeregistry to use to complete the lookup.
        """
        return git.Repo(self.GetWorkingPath(mapper))

    def GetWorkingAssets(self, mapper, recursive = False):
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
            asset = fiepipelib.gitstorage.workingasset.workingasset(submodule)
            ret.append(asset)
        return ret





class localworkingdirectoryroots(fiepipelib.container.abstractcomponent):

    _roots = None

    def DeserializeJSONData(self, data):
        self._roots.clear()
        rootsdata = data['roots']
        for rootdata in rootsdata:
            self._roots.append(RootFromJSONData(rootdata))
        return super().DeserializeJSONData(data)

    def SerializeJSONData(self):
        ret = super().SerializeJSONData()
        rootsdata = []
        for root in self._roots:
            rootsdata.append(RootToJSONData(root))
        ret['roots'] = rootsdata
        return ret

    def GetComponentName(self):
        return "git_local_working_directory_roots"

    def __init__(self, conf):
        """@param conf: a fiepipelib.container.localconfiguration to use to store data.
        """
        assert isinstance(conf, fiepipelib.container.localconfiguration)
        super().__init__(conf)
        self._roots = []

    def GetRoots(self):
        return self._roots.copy()

    def SetRoots(self, roots):
        self._roots.clear()
        self._roots.extend(roots)
