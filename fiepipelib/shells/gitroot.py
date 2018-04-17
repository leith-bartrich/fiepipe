import cmd2
import fiepipelib.shells.abstract
import git
import fiepipelib.gitstorage.routines.lfs
import fiepipelib.gitstorage.routines.repo
import os
import os.path
import pathlib
import shutil
import functools
import fiepipelib.gitstorage.root
import fiepipelib.gitstorage.workingroot
import fiepipelib.shells.container
import typing



class Shell(fiepipelib.shells.abstract.Shell):

    _repo = None

    _localUser = None
    _entity = None
    _site = None
    _container = None
    _containerConfig = None
    _id = None

    def getPluginNameV1(self):
        return "gitroot"

    def __init__(self, id, container, containerConfig, localUser, entity, site):
        assert isinstance(container, fiepipelib.container.container)
        assert isinstance(containerConfig, fiepipelib.container.localconfiguration)
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        assert isinstance(site,fiepipelib.abstractsite.abstractsite)

        self._localUser = localUser
        self._entity = entity
        self._site = site
        self._container = container
        self._containerConfig = containerConfig
        self._id = id

        root = self._GetRoot()
        config = self._GetConfig()
        #reg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        dir = config.GetWorkingPath(mapper)
        if not os.path.exists(dir):
            os.makedirs(dir)
        elif not os.path.isdir(dir):
            print("Path exists but is not a directory.")
            raise FileExistsError(dir)
        os.chdir(dir)

        super().__init__()
        
        self.AddSubmenu(AssetsCommand(self), "assets", [])

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join(['pipe',self._entity.GetFQDN(),self._site.GetName(),self._container.GetShortName(),self._GetRoot().GetName()])

    def mounted_backing_store_completion(self,text,line,begidx,endidx):
        ret = []
        storageMapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        backingVols = storageMapper.GetMountedBackingStorage()
        for backingVol in backingVols:
            ret.append(backingVol.GetName())
        return ret

    def mounted_archive_completion(self,text,line,begidx,endidx):
        ret = []
        storageMapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        backingVols = storageMapper.GetMountedBackingStorage()
        for backingVol in backingVols:
            ret.append(backingVol.GetName())
        return ret

    def _GetRoot(self):
        """Gets the root from the container
        """
        component = fiepipelib.gitstorage.root.workingdirectoryroots(self._container)
        component.Load()
        roots = component.GetRoots()
        root = None
        for r in roots:
            assert isinstance(r, fiepipelib.gitstorage.root.root)
            if r.GetID() == self._id:
                root = r
            if root != None:
                break
        if root == None:
            print("No such root in the loaded container.  You should probably exit this shell.")
            raise LookupError(self._id)
        assert isinstance(root, fiepipelib.gitstorage.root.root)
        return root

    def _GetConfig(self):
        """Gets the local configuration of the root from the container's local configuration.
        """
        configcomponent = fiepipelib.gitstorage.workingroot.localworkingdirectoryroots(self._containerConfig)
        configcomponent.Load()
        configuredroots = configcomponent.GetRoots()
        configedroot = None
        for c in configuredroots:
            assert isinstance(c, fiepipelib.gitstorage.workingroot.workingroot)
            if c.GetID() == self._id:
                configedroot = c
            if configedroot != None:
                break
        if configedroot == None:
            print("No such local root configuartion.  You should probably exit this shell.")
            raise LookupError(id)
        assert isinstance(configedroot, fiepipelib.gitstorage.workingroot.workingroot)
        
        return configedroot
    
    def _GetLocalRepoPath(self):
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        #volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        dir = config.GetWorkingPath(mapper)
        if os.path.exists(dir):
            if os.path.isdir(dir):
                os.chdir(dir)
        return dir
    
    def _GetLocalRepo(self):
        """
        Gets the local repository if it exists.  Throws variously if there is a problem.  Calls 'is_dirty' internally.
        """
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        #volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        rep = config.GetRepo(mapper)
        if not os.path.exists(rep.working_tree_dir):
            print("Working tree doesn't exist: " + rep.working_tree_dir)
            raise FileNotFoundError(rep.working_tree_dir)
        if not os.path.isdir(rep.working_tree_dir):
            print("Working tree path isn't a directory: " + rep.working_tree_dir)
            raise NotADirectoryError(rep.working_tree_dir)
        rep.is_dirty()
        return rep


    def do_init_new(self,args):
        """Initializes a brand new repository for the root with an empty working tree.

        Should only be executed once by one person.  Everyone else should be retrieving it via other means.

        If run on an existing repository, it will warn appropriately.

        Usage: init_new
        """
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        config = self._GetConfig()
        dir = config.GetWorkingPath(mapper)

        if fiepipelib.gitstorage.routines.repo.RepoExists(dir):
            print(self.colorize("Already exists.","red"))
            return

        print("Initializing Repo.")
        repo = fiepipelib.gitstorage.routines.repo.InitWorkingTreeRoot(dir)
        print("Installing LFS to Repo.")
        fiepipelib.gitstorage.routines.lfs.InstallLFSRepo(repo)
        print("Setting up .gitignore")
        fiepipelib.gitstorage.routines.ignore.CheckCreateIgnore(repo)
        print("Commiting to head")
        repo.index.commit("Initial commit.")
        os.chdir(dir)
        return

    complete_init_new_split = mounted_backing_store_completion

    def do_init_new_split(self, args):
        """Initializes a brand new repository for the root with an empty working tree and a repository on a
        specified backing store.  See init_new for other details.

        Usage: init_new_split [volume]

        arg volume: the name of a mounted backing store to use for the split repository
        """

        if args == None:
            print("No volume specified.")
            return
        if args == "":
            print("No volume specified.")
            return

        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        #volReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        root = self._GetRoot()
        vol = mapper.GetMountedBackingStorageByName(args)

        assert isinstance(config, fiepipelib.gitstorage.workingroot.workingroot)

        print("Creating repository on backing volume: " + vol.GetName() + " " + vol.GetPath())
        backingRep = root.CreateRepositoryOnBackingVolume(vol)

        workingtreepath = config.GetWorkingPath(volReg)
        print("Creating working tree on working volume: " + root.GetName() + " " + workingtreepath)
        backingRep.git.worktree("add", workingtreepath)
        workingRepo = git.Repo(workingtreepath)

        print("Installing LFS to Repo.")
        fiepipelib.gitstorage.routines.lfs.InstallLFSRepo(workingRepo)
        print("Setting up .gitignore")
        fiepipelib.gitstorage.routines.ignore.CheckCreateIgnore(workingRepo)
        print("Commiting to head")
        workingRepo.index.commit("Initial commit.")
        os.chdir(workingtreepath)


    def do_pull_from_archives(self, args):
        """Clones the working tree from any found on currenlty mounted archives.

        Fails variously if there is a problem.

        Usage: pull_from_archives
        """

        #path
        #volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        localPath = self._GetLocalRepoPath()

        #source
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        root = self._GetRoot()
        vols = root.FindOnMountedArchiveVolumes(mapper)
        if len(vols) == 0:
            print(self.colorize("Root not found on any mounted archive.  Can't clone it to a working tree.","red"))
            return
        #We grab the first. [shrug]
        backingRep = root.GetRepositoryOnArchiveVolume(vols[0],False)

        #clone
        print("Cloning to local working tree...")
        backingRep.clone(localPath)
        os.chdir(localPath)

    complete_pull_split_from_archives = mounted_backing_store_completion

    def do_pull_split_from_archives(self, args):
        """Creates a split wokring tree from the specified backing store.

        Usage: create_split_worktree [volume]

        arg volume: The backing store volume to use.
        """
        if args == None:
            print("No volume specified.")
            return
        if args == "":
            print("No volume specified.")
            return

        #path
        #volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        localPath = self._GetLocalRepoPath()

        #source
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        root = self._GetRoot()
        
        #find archive
        vols = root.FindOnMountedArchiveVolumes(mapper)
        if len(vols) == 0:
            print(self.colorize("Root not found on any mounted archive.  Can't clone it to a working tree.","red"))
            return
        #We grab the first. [shrug]
        archiveRep = root.GetRepositoryOnArchiveVolume(vols[0],False)

        #create repo
        backingVol = mapper.GetMountedBackingStorageByName(args)
        backingPath = root.GetPathForBackingVolume(backingVol)
        archiveRep.clone(backingPath)
        backingRepo = root.GetRepositoryOnBackingVolume(backingVol,False)

        #create worktree
        backingRepo.git.worktree("add", localPath)
        os.chdir(localPath)

    complete_archive_local = mounted_archive_completion

    def do_archive_local(self, args):
        """Clones the local working tree repository and assets to the given archive.
        
        Skips assets that are not checked out.

        Generally used to populate or update an archive with the current local working set's state and history.

        WARNING: This is not a comprehensive backup of the full project.

        Usage: archive_local [name]

        arg name: The name of the archive to clone to.
        """
        if args == None:
            print("No archive name specified.")
            return
        if args == "":
            print("No archive name specified.")
            return

        storageMapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        vol = storageMapper.GetMountedArchivalStorageByName(args)
        config = self._GetConfig()
        root = self._GetRoot()

        fiepipelib.gitstorage.routines.workingdirectoryroot.PushRootToArchiveRecursive(root,config,vol,self._localUser)


    complete_archive_full = mounted_archive_completion

    def do_archive_full(self,args):
        """Archives the working tree and its history to the given archive, including all assets.
        
        Errors if all assets are not checked out, hence ensuring a full project backup.

        WARNING: Currently, it's possible some assets will be skipped if they're not part of the current working tree.  e.g. you deleted them at some point from the project.

        Usage: archive_full [name]

        arg name: The name of the archive to clone to.

        Errors if the root is not fully checked out.
        """
        if args == None:
            print("No archive name specified.")
            return
        if args == "":
            print("No archive name specified.")
            return

        config = self._GetConfig()
        if not fiepipelib.gitstorage.routines.workingdirectoryroot.IsFullyCheckedOut(config,self._localUser):
            print(self.colorize("Root not fully checked out.","red"))
            return

        return self.do_archive_local(args)


    #def asset_completion(self,text,line,begidx,endidx):
        #ret = []
        #localconfig = self._GetConfig()
        ##storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        #mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        #assets = localconfig.GetWorkingAssets(mapper,True)
        #for asset in assets:
            #id = asset.GetAsset().GetID()
            #if id.lower().startswith(text.lower()):
                #ret.append(id)
            #path = asset.GetSubmodule().path
            #if path.lower().startswith(text.lower()):
                #ret.append(path)
        #return ret

    def _get_asset(self, pathorid):
        """Returns a workingasset for a path or id from this root, if possible.
        """
        #storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        localconfig = self._GetConfig()
        assets = localconfig.GetWorkingAssets(mapper,True)
        for asset in assets:

            id = asset.GetAsset().GetID()
            if id.lower() == pathorid.lower():
                return asset

            path = asset.GetSubmodule().path
            if os.path.samefile(path,pathorid):
                return asset

        print("No asset found: " + pathorid)
        raise KeyError("Asset not found: "  + pathorid)


    #complete_asset_shell = asset_completion

    #def do_asset_shell(self, args):
        #"""Enters a subshell for working with the given asset

        #Usage: asset_shell [asset]

        #arg asset: either the subpath or id of an asset in the current root.
        #"""

        #if args == None:
            #print("No asset specified.")
            #return

        #if args == "":
            #print("No asset specified.")
            #return

        #asset = self._get_asset(args)
        #path = asset.GetSubmodule().path
        #shell = fiepipelib.shells.gitasset.Shell(asset,path,self._container,self._containerConfig,self._GetRoot(),self._GetConfig(),self._localUser,self._entity,self._site)
        #shell.cmdloop()

    #complete_ash = asset_completion

    #def ash(self, args):
        #"""Alias for asset_shell command
        #"""
        #self.do_asset_shell(args)

    #complete_create_asset = functools.partial(cmd2.Cmd.path_complete)

    #def do_create_asset(self, args):
        #"""Create a new asset at the given path

        #Usage: create_asset [path]

        #arg path: The subpath to an asset to create.  It will be created whether the files/dir already exist, or not.
        #"""

        #if args == None:
            #print("No path specified.")
            #return

        #if args == "":
            #print("No path specified.")
            #return

        ##storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        #mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        #config = self._GetConfig()
        #rootPath = os.path.abspath(config.GetWorkingPath(mapper))

        #if os.path.isabs(args):
            #if not args.startswith(rootPath):
                #print(self.colorize("Absolute path isn't inside root path: " + args,"red"))
                #return
            #else:
                #args = os.path.relpath(args,rootPath)
        ##args is now certainly a relative path

        #rep = self._GetLocalRepo()

        #(creationRepo,creationSubPath) = fiepipelib.gitstorage.routines.submodules.CanCreateSubmodule(rep,args)

        #if creationRepo == None:
            #print( self.colorize("Cannot create asset at the given path.","red"))
            #print("It might exist already.  Or it might be in a submodule that's not currently checked out.")
            #return


        #newid = fiepipelib.gitstorage.asset.NewID()
        #print("Creating new submodule for asset.")
        #submod = fiepipelib.gitstorage.routines.submodules.CreateFromSubDirectory(creationRepo,creationSubPath,newid)


    #complete_delete_asset = asset_completion

    #def do_delete_asset(self, args):
        #"""Deletes an asset from the root.  WARNING: this is not just a local change.  You are actually removing the asset from the project.

        #Doesn't clean the asset form backing stores.  If you really screw up, you can still recover from old versions of the root so long
        #as the asset's repositories still exist in the system and the submodule entry is recreated with the same name|id.

        #Usage: delete_asset [path|id]

        #arg path|id:  The subpath or id of the asset do delete.
        #"""

        #if args == None:
            #print("No asset specified.")
            #return
        #if args == "":
            #print("No asset specified.")
            #return

        #workingAsset = self._get_asset(args)
        #rootRepo = self._GetLocalRepo()
        #fiepipelib.gitstorage.routines.submodules.Remove(rootRepo,workingAsset.GetAsset().GetID())
        
    def _print_workingasset(self, asset):
        assert isinstance(asset, fiepipelib.gitstorage.workingasset.workingasset)
        existsText = self.colorize("absent", "yellow")
        statusText = "---"
        if asset.GetSubmodule().module_exists():
            existsText = self.colorize("exists", "green")
            rep = asset.GetSubmodule().module()
            assert isinstance(rep, git.Repo)
            if rep.is_dirty():
                statusText = self.colorize("dirty", "red")
            else:
                statusText = self.colorize("clean", "green")
        print( "asset: {0} - {1} - {2} - {3}".format( asset.GetSubmodule().path, asset.GetAsset().GetID(), existsText, statusText) )

    def _print_root(self):
        root = self._GetRoot()
        config = self._GetConfig()
        existsText = self.colorize("absent", "yellow")
        statusText = "---"
        if fiepipelib.gitstorage.routines.repo.RepoExists(self._GetLocalRepoPath()):
            existsText = self.colorize("exists", "green")
            rep = self._GetLocalRepo()
            assert isinstance(rep, git.Repo)
            if rep.is_dirty():
                statusText = self.colorize("dirty", "red")
            else:
                statusText = self.colorize("clean", "green")
        print( "root: {0} - {1} - {2} - {3}".format( self._GetLocalRepoPath(), root.GetID(), existsText, statusText) )

    def do_status(self, args):
        #reg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        config = self._GetConfig()
        self._print_root()

    def do_status_all(self, args):
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
        config = self._GetConfig()
        assets = config.GetWorkingAssets(mapper,True)
        self._print_root()
        for asset in assets:
            self._print_workingasset(asset)

    def do_delete_worktree(self, args):
        """Deletes the worktree from disk.

        If you have a split worktree, this will not delete the repository on the backing volume.  Just the worktree.

        Will confirm if the worktree is dirty, or if the worktree is not split.  Just incase.

        Usage: delete_worktree
        """
        dir = self._GetLocalRepoPath()
        pardir = str(pathlib.Path(dir).parent)

        if not pathlib.Path(dir).exists():
            print("Doesn't exist.")
            return

        try:
            rep = self._GetLocalRepo()
        except git.InvalidGitRepositoryError:
            print("Invalid git repository.  Deleting contents of folder.")
            os.chdir(pardir)
            shutil.rmtree(dir)
            return
        
            

        if not rep.has_separate_working_tree():
            reply = self.AskTrueFalseQuestion("The repository is inside the worktree and it will be deleted too.  Are you sure?")
            if reply == False:
                print("Aboriting.")
                return

        if rep.is_dirty():
            reply = self.AskTrueFalseQuestion("The root is dirty and probably has uncommited changes.  Are you sure?")
            if reply == False:
                print("Aboriting.")
                return

        dir = rep.working_dir
        rep.close()
        os.chdir(pardir)
        shutil.rmtree(dir)
        
        
class AssetsCommand(fiepipelib.shells.abstract.Shell):
    
    _rootShell = None
    
    def __init__(self, rootShell:Shell):
        self._rootShell = rootShell
        super().__init__()
        assert isinstance(self._rootShell, Shell)
        
    def getPluginNameV1(self):
        return "gitassets_command"
    
    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join([self._rootShell.GetBreadCrumbsText(),"gitassets_command"])
    
    def asset_completion(self,text,line,begidx,endidx):
        ret = []
        workingRoot = self._rootShell._GetConfig()
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._rootShell._localUser)
        assets = workingRoot.GetWorkingAssets(mapper,True)
        for asset in assets:
            id = asset.GetAsset().GetID()
            if id.lower().startswith(text.lower()):
                ret.append(id)
            path = asset.GetSubmodule().path
            if path.lower().startswith(text.lower()):
                ret.append(path)
        return ret
    
    complete_delete = asset_completion
    
    def do_delete(self, args):
        """Deletes an asset from the root.  WARNING: this is not just a local change.  You are actually removing the asset from the project.

        Doesn't clean the asset form backing stores.  If you really screw up, you can still recover from old versions of the root so long
        as the asset's repositories still exist in the system and the submodule entry is recreated with the same name|id.

        Usage: delete [path|id]

        arg path|id:  The subpath or id of the asset do delete.
        """
        
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            print("No asset specified.")
            return

        workingAsset = self._rootShell._get_asset(args[0])
        rootRepo = self._rootShell._GetLocalRepo()
        fiepipelib.gitstorage.routines.submodules.Remove(rootRepo,workingAsset.GetAsset().GetID())
    
    complete_create_asset = functools.partial(cmd2.Cmd.path_complete)
    
    def do_create(self, args):
        """Create a new asset at the given path

        Usage: create [path]

        arg path: The subpath to an asset to create.  It will be created whether the files/dir already exist, or not.
        """
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            print("No path specified.")
            return

        #storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
        mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._rootShell._localUser)
        config = self._rootShell._GetConfig()
        rootPath = os.path.abspath(config.GetWorkingPath(mapper))

        if os.path.isabs(args[0]):
            if not args[0].startswith(rootPath):
                print(self.colorize("Absolute path isn't inside root path: " + args[0],"red"))
                return
            else:
                args[0] = os.path.relpath(args[0],rootPath)
        #args is now certainly a relative path

        rep = self._rootShell._GetLocalRepo()

        (creationRepo,creationSubPath) = fiepipelib.gitstorage.routines.submodules.CanCreateSubmodule(rep,args[0])

        if creationRepo == None:
            self.perror( self.colorize("Cannot create asset at the given path.","red"))
            self.perror("It might exist already.  Or it might be in a submodule that's not currently checked out.")
            return


        newid = fiepipelib.gitstorage.asset.NewID()
        self.pfeedback("Creating new submodule for asset.")
        submod = fiepipelib.gitstorage.routines.submodules.CreateFromSubDirectory(creationRepo,creationSubPath,newid)
        
    complete_enter = asset_completion

    def do_enter(self, args):
        """Enters a subshell for working with the given asset

        Usage: asset_shell [asset]

        arg asset: either the subpath or id of an asset in the current root.
        """
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            print("No asset specified.")
            return

        asset = self._rootShell._get_asset(args[0])
        path = asset.GetSubmodule().path
        shell = fiepipelib.shells.gitasset.Shell(asset,path,self._rootShell._container,self._rootShell._containerConfig,self._rootShell._GetRoot(),self._rootShell._GetConfig(),self._rootShell._localUser,self._rootShell._entity,self._rootShell._site)
        shell.cmdloop()
