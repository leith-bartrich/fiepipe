import cmd2
import fiepipelib.shells.abstract
import git
import fiepipelib.gitstorage.routines.lfs
import fiepipelib.gitstorage.routines.repo
import os
import os.path

class Shell(fiepipelib.shells.abstract.Shell):


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
        assert isinstance(root, fiepipelib.gitstorage.root.root)
        assert isinstance(workingroot, fiepipelib.gitstorage.workingroot.workingroot)
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


        super().__init__()

        os.chdir(self._workingAsset.GetSubmodule().abspath)

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join(['pipe',self._entity.GetFQDN(),self._site.GetName(),self._container.GetShortName(),self._subpath])

    def do_checkout(self, args):
        """Checks out this asset from backing stores if available.

        Usage: checkout
        """
        if self._workingAsset.IsCheckedOut():
            self.perror("Already checked out.")
            return
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        archiveVolumes = self._workingAsset.GetAsset().FindOnMountedArchiveVolumes(mapper)
        if len(archiveVolumes) == 0:
            print(self.colorize("Asset not found on any archives.","red"))
            return
        archiveVolume = archiveVolumes[0]
        fiepipelib.gitstorage.routines.submodules.ChangeURL(self._workingRoot.GetRepo(mapper),self._workingAsset.GetAsset().GetID(),self._workingAsset.GetAsset().GetPathForArchiveVolume(archiveVolume),revertGitModulesFile=True)
        fiepipelib.gitstorage.routines.submodules.Checkout(self._workingAsset.GetAsset().GetRepositoryOnArchiveVolume(archiveVolume),self._workingAsset.GetSubmodule(),False)
        self.do_update(None)

    def do_update(self, args):
        """Updates this asset from any mounted archive volumes.
        
        Usage: update
        """
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        archiveVolumes = self._workingAsset.GetAsset().FindOnMountedArchiveVolumes(mapper)
        if len(archiveVolumes) == 0:
            print(self.colorize("Asset not found on any backing stores.","red"))
            return

        for archiveVolume in archiveVolumes:
            fiepipelib.gitstorage.routines.submodules.ChangeURL(self._workingRoot.GetRepo(mapper),self._workingAsset.GetAsset().GetID(),self._workingAsset.GetAsset().GetPathForArchiveVolume(archiveVolume),revertGitModulesFile=True)
            fiepipelib.gitstorage.routines.submodules.Update(self._workingAsset.GetAsset().GetRepositoryOnArchiveVolume(archiveVolume),self._workingAsset.GetSubmodule(),False)

    def do_up(self, args):
        """Alias for update."""
        self.do_update(args)
        

    def do_status(self, args):
        """Prints git status of the asset.
        
        Usage: status
        """
        submod = self._workingAsset.GetSubmodule()
        if not submod.module_exists():
            print(self.colorize("not checked out.","yellow"))
            return
        rep = submod.module()
        assert isinstance(rep, git.Repo)
        rep.git.status()
        
    def do_stat(self,args):
        """Alias for status command."""
        self.do_status(args)


    def do_cull_dbhash_db(self):
        """Culls useless entries in the databasehash database for this asset.  A maintnance task.
        
        Harmless to call it.  It might speed up some sqlite digital asset work.
        
        Usage: cull_dbhash_db
        """
        man = fiepipelib.assetdata.databasehash.AssetDatabaseManager(
            self._workingAsset)
        man.Cull()
        
      

