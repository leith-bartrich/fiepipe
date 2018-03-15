import cmd2
import fiepipelib.shells.abstract
import git
import fiepipelib.gitstorage.routines.lfs
import fiepipelib.gitstorage.routines.repo
import os
import os.path

class Shell(fiepipelib.shells.abstract.Shell):

    prompt = "pipe/entity/site/container/asset>"

    _localUser = None
    _entity = None
    _site = None
    _container = None
    _containerConfig = None
    _workingAsset = None
    _subpath = None
    _root = None
    _workingRoot = None

    def getPluginNameV1(self):
        return "gitasset"

    def __init__(self, workingasset, subpath, container, containerConfig, root, workingroot, localUser, entity, site):
        assert isinstance(container, fiepipelib.container.container)
        assert isinstance(containerConfig, fiepipelib.container.localconfiguration)
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        assert isinstance(site,fiepipelib.abstractsite.abstractsite)
        assert isinstance(root, fiepipelib.gitstorage.workingdirectoryroot.root)
        assert isinstance(root, fiepipelib.gitstorage.localworkingdirectoryroot.workingroot)
        assert isinstance(workingasset, fiepipelib.gitstorage.workingasset.workingasset)

        self._localUser = localUser
        self._entity = entity
        self._site = site
        self._container = container
        self._containerConfig = containerConfig
        self._workingAsset = workingasset
        self._subpath = subpath
        self._root = root
        self._workingRoot = workingroot

        prompt = ("/".join(["pipe",entity.GetFQDN(),site.GetName(),container.GetShortName(),subpath])) + ">"

        super().__init__()

        os.chdir(self._workingAsset.GetSubmodule().abspath)

    def do_checkout(self, args):
        """Checks out this asset from backing stores if available.

        Usage: checkout
        """
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        backingVolumes = self._workingAsset.GetAsset().FindOnMountedBackingVolumes(mapper)
        if len(backingVolumes) == 0:
            print(self.colorize("Asset not found on any backing stores.","red"))
            return
        backingVolume = backingVolumes[0]
        localReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        fiepipelib.gitstorage.routines.submodules.ChangeURL(self._workingRoot.GetRepo(localReg),self._workingAsset.GetAsset().GetID(),self._workingAsset.GetAsset().GetPathForBackingVolume(backingVolume),revertGitModulesFile=True)
        fiepipelib.gitstorage.routines.submodules.Checkout(self._workingRoot.GetRepo(localReg),self._workingAsset.GetSubmodule(),False)
        self.do_update(None)

    def do_update(self, args):
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        backingVolumes = self._workingAsset.GetAsset().FindOnMountedBackingVolumes(mapper)
        if len(backingVolumes) == 0:
            print(self.colorize("Asset not found on any backing stores.","red"))
            return

        localReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)

        for backingVolume in backingVolumes:
            fiepipelib.gitstorage.routines.submodules.ChangeURL(self._workingRoot.GetRepo(localReg),self._workingAsset.GetAsset().GetID(),self._workingAsset.GetAsset().GetPathForBackingVolume(backingVolume),revertGitModulesFile=True)
            fiepipelib.gitstorage.routines.submodules.Update(self._workingRoot.GetRepo(localReg),self._workingAsset.GetSubmodule(),False)

    def do_status(self, args):
        submod = self._workingAsset.GetSubmodule()
        if not submod.module_exists():
            print(self.colorize("not checked out.","yellow"))
            return
        rep = submod.module()
        assert isinstance(rep, git.Repo)
        rep.git.status()



      

