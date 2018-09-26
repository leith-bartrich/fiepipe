import functools
import typing

import cmd2

import fiepipelib.shells.AbstractShell
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fiepipelib.gitstorage.shells.gitasset import Shell as GitAssetShell
from fiepipelib.gitstorage.shells.vars.root_id import RootIDVarCommand
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines


class Shell(fiepipelib.shells.AbstractShell.AbstractShell):
    _container_id_var: ContainerIDVariableCommand = None
    _root_id_var: RootIDVarCommand = None

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('gitroot')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_routines()
        routines.load()
        container = routines.container
        fqdn = container.GetFQDN()
        container_name = container.GetShortName()
        root = routines.root
        root_name = root.GetName()
        return self.prompt_separator.join(['fiepipe', fqdn, container_name, root_name])

    def __init__(self, root_id, container_id):
        self._container_id_var = ContainerIDVariableCommand(container_id)
        self.add_variable_command(self._container_id_var, "container", [], False)
        self._root_id_var = RootIDVarCommand(root_id)
        self.add_variable_command(self._root_id_var, "root", [], False)

        super(Shell, self).__init__()

        routines = self.get_routines()
        routines.load()
        routines.check_create_change_dir()

        assets_command = AssetsCommand(self)
        self.add_submenu(assets_command, "assets", ['as'])

    def get_routines(self) -> GitRootRoutines:
        return GitRootRoutines(self._container_id_var.get_value(), self._root_id_var.get_value(),
                               feedback_ui=self.get_feedback_ui(),
                               true_false_question_ui=self.get_true_false_question_modal_ui())

    def mounted_backing_store_completion(self, text, line, begidx, endidx):
        ret = []
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        storageMapper = localstoragemapper(user)
        backingVols = storageMapper.GetMountedBackingStorage()
        for backingVol in backingVols:
            if (backingVol.GetName().startswith(text)):
                ret.append(backingVol.GetName())
        return ret

    #
    # def mounted_archive_completion(self, text, line, begidx, endidx):
    #     ret = []
    #     storageMapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     backingVols = storageMapper.GetMountedBackingStorage()
    #     for backingVol in backingVols:
    #         ret.append(backingVol.GetName())
    #     return ret

    def do_init_new(self, args):
        """Initializes a brand new repository for the root with an empty working tree.

        Should only be executed once by one person.  Everyone else should be retrieving it via other means.

        If run on an existing repository, it will warn appropriately.

        Usage: init_new
        """
        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.init_new())

    complete_init_new_split = mounted_backing_store_completion

    def do_init_new_split(self, args):
        """Initializes a brand new repository for the root with an empty working tree and a repository on a
        specified backing store.  See init_new for other details.

        Usage: init_new_split [volume]

        arg volume: the name of a mounted backing store to use for the split repository
        """

        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No volume specified.")
            return

        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        mapper = localstoragemapper(user)

        vol = mapper.GetMountedBackingStorageByName(args[0])

        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.init_new_split(vol))

    def do_checkout_from_split(self, args):
        """Checks out a worktree for the root from a repository on a
        specified backing store.

        Usage: checkout_from_split [volume]

        arg volume: the name of a mounted backing store that contains the split repository
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No volume specified.")
            return

        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        mapper = localstoragemapper(user)

        vol = mapper.GetMountedBackingStorageByName(args[0])

        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.checkout_worktree_from_backing_routine(vol))

    def do_delete_worktree(self, args):
        """Deletes the worktree from disk.

        If you have a split worktree, this will not delete the repository on the backing volume.  Just the worktree.

        Will confirm if the worktree is dirty, or if the worktree is not split.  Just incase.

        Usage: delete_worktree
        """
        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.delete_worktree_routine())

    # def do_pull_from_archives(self, args):
    #     """Clones the working tree from any found on currenlty mounted archives.
    #
    #     Fails variously if there is a problem.
    #
    #     Usage: pull_from_archives
    #     """
    #
    #     # path
    #     # volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
    #     config = self._GetConfig()
    #     localPath = self._GetLocalRepoPath()
    #
    #     # source
    #     mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     root = self._GetRoot()
    #     vols = root.FindOnMountedArchiveVolumes(mapper)
    #     if len(vols) == 0:
    #         print(self.colorize("Root not found on any mounted archive.  Can't clone it to a working tree.", "red"))
    #         return
    #     # We grab the first. [shrug]
    #     backingRep = root.GetRepositoryOnArchiveVolume(vols[0], False)
    #
    #     # clone
    #     print("Cloning to local working tree...")
    #     backingRep.clone(localPath)
    #     os.chdir(localPath)

    # complete_pull_split_from_archives = mounted_backing_store_completion
    #
    # def do_pull_split_from_archives(self, args):
    #     """Creates a split wokring tree from the specified backing store.
    #
    #     Usage: create_split_worktree [volume]
    #
    #     arg volume: The backing store volume to use.
    #     """
    #     if args == None:
    #         print("No volume specified.")
    #         return
    #     if args == "":
    #         print("No volume specified.")
    #         return
    #
    #     # path
    #     # volRegistry = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
    #     config = self._GetConfig()
    #     localPath = self._GetLocalRepoPath()
    #
    #     # source
    #     mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     root = self._GetRoot()
    #
    #     # find archive
    #     vols = root.FindOnMountedArchiveVolumes(mapper)
    #     if len(vols) == 0:
    #         print(self.colorize("Root not found on any mounted archive.  Can't clone it to a working tree.", "red"))
    #         return
    #     # We grab the first. [shrug]
    #     archiveRep = root.GetRepositoryOnArchiveVolume(vols[0], False)
    #
    #     # create repo
    #     backingVol = mapper.GetMountedBackingStorageByName(args)
    #     backingPath = root.GetPathForBackingVolume(backingVol)
    #     archiveRep.clone(backingPath)
    #     backingRepo = root.GetRepositoryOnBackingVolume(backingVol, False)
    #
    #     # create worktree
    #     backingRepo.git.worktree("add", localPath)
    #     os.chdir(localPath)

    # complete_archive_local = mounted_archive_completion

    # def do_archive_local(self, args):
    #     """Clones the local working tree repository and assets to the given archive.
    #
    #     Skips assets that are not checked out.
    #
    #     Generally used to populate or update an archive with the current local working set's state and history.
    #
    #     WARNING: This is not a comprehensive backup of the full project.
    #
    #     Usage: archive_local [name]
    #
    #     arg name: The name of the archive to clone to.
    #     """
    #     if args == None:
    #         print("No archive name specified.")
    #         return
    #     if args == "":
    #         print("No archive name specified.")
    #         return
    #
    #     storageMapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     vol = storageMapper.GetMountedArchivalStorageByName(args)
    #     config = self._GetConfig()
    #     root = self._GetRoot()
    #
    #     fiepipelib.git.routines.workingdirectoryroot.PushRootToArchiveRecursive(root, config, vol, self._localUser)

    # complete_archive_full = mounted_archive_completion

    # def do_archive_full(self, args):
    #     """Archives the working tree and its history to the given archive, including all assets.
    #
    #     Errors if all assets are not checked out, hence ensuring a full project backup.
    #
    #     WARNING: Currently, it's possible some assets will be skipped if they're not part of the current working tree.  e.g. you deleted them at some point from the project.
    #
    #     Usage: archive_full [name]
    #
    #     arg name: The name of the archive to clone to.
    #
    #     Errors if the root is not fully checked out.
    #     """
    #     if args == None:
    #         print("No archive name specified.")
    #         return
    #     if args == "":
    #         print("No archive name specified.")
    #         return
    #
    #     config = self._GetConfig()
    #     if not fiepipelib.git.routines.workingdirectoryroot.IsFullyCheckedOut(config, self._localUser):
    #         print(self.colorize("Root not fully checked out.", "red"))
    #         return
    #
    #     return self.do_archive_local(args)

    # def asset_completion(self,text,line,begidx,endidx):
    # ret = []
    # localconfig = self._GetConfig()
    ##storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
    # mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    # assets = localconfig.GetWorkingAssets(mapper,True)
    # for asset in assets:
    # id = asset.GetAsset().GetID()
    # if id.lower().startswith(text.lower()):
    # ret.append(id)
    # path = asset.GetSubmodule().path
    # if path.lower().startswith(text.lower()):
    # ret.append(path)
    # return ret

    # def _get_asset(self, pathorid):
    #     """Returns a workingasset for a path or id from this root, if possible.
    #     """
    #     # storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
    #     mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     localconfig = self._GetConfig()
    #     assets = localconfig.GetWorkingAssets(mapper, True)
    #     for asset in assets:
    #
    #         id = asset.GetAsset().GetID()
    #         if id.lower() == pathorid.lower():
    #             return asset
    #
    #         path = asset.GetSubmodule().path
    #         if os.path.samefile(path, pathorid):
    #             return asset
    #
    #     print("No asset found: " + pathorid)
    #     raise KeyError("Asset not found: " + pathorid)

    # complete_asset_shell = asset_completion

    # def do_asset_shell(self, args):
    # """Enters a subshell for working with the given asset

    # Usage: asset_shell [asset]

    # arg asset: either the subpath or id of an asset in the current root.
    # """

    # if args == None:
    # print("No asset specified.")
    # return

    # if args == "":
    # print("No asset specified.")
    # return

    # asset = self._get_asset(args)
    # path = asset.GetSubmodule().path
    # shell = fiepipelib.shells.gitasset.Shell(asset,path,self._container,self._containerConfig,self._GetRoot(),self._GetConfig(),self._localUser,self._entity,self._site)
    # shell.cmdloop()

    # complete_ash = asset_completion

    # def ash(self, args):
    # """Alias for asset_shell command
    # """
    # self.do_asset_shell(args)

    # complete_create_asset = functools.partial(cmd2.Cmd.path_complete)

    # def do_create_asset(self, args):
    # """Create a new asset at the given path

    # Usage: create_asset [path]

    # arg path: The subpath to an asset to create.  It will be created whether the files/dir already exist, or not.
    # """

    # if args == None:
    # print("No path specified.")
    # return

    # if args == "":
    # print("No path specified.")
    # return

    ##storageReg = fiepipelib.storage.localvolume.localvolumeregistry(self._localUser)
    # mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    # config = self._GetConfig()
    # rootPath = os.path.abspath(config.GetWorkingPath(mapper))

    # if os.path.isabs(args):
    # if not args.startswith(rootPath):
    # print(self.colorize("Absolute path isn't inside root path: " + args,"red"))
    # return
    # else:
    # args = os.path.relpath(args,rootPath)
    ##args is now certainly a relative path

    # rep = self._GetLocalRepo()

    # (creationRepo,creationSubPath) = fiepipelib.gitstorage.routines.submodules.CanCreateSubmodule(rep,args)

    # if creationRepo == None:
    # print( self.colorize("Cannot create asset at the given path.","red"))
    # print("It might exist already.  Or it might be in a submodule that's not currently checked out.")
    # return

    # newid = fiepipelib.gitstorage.asset.NewID()
    # print("Creating new submodule for asset.")
    # submod = fiepipelib.gitstorage.routines.submodules.CreateFromSubDirectory(creationRepo,creationSubPath,newid)

    # complete_delete_asset = asset_completion

    # def do_delete_asset(self, args):
    # """Deletes an asset from the root.  WARNING: this is not just a local change.  You are actually removing the asset from the project.

    # Doesn't clean the asset form backing stores.  If you really screw up, you can still recover from old versions of the root so long
    # as the asset's repositories still exist in the system and the submodule entry is recreated with the same name|id.

    # Usage: delete_asset [path|id]

    # arg path|id:  The subpath or id of the asset do delete.
    # """

    # if args == None:
    # print("No asset specified.")
    # return
    # if args == "":
    # print("No asset specified.")
    # return

    # workingAsset = self._get_asset(args)
    # rootRepo = self._GetLocalRepo()
    # fiepipelib.gitstorage.routines.submodules.Remove(rootRepo,workingAsset.GetAsset().GetID())


class AssetsCommand(fiepipelib.shells.AbstractShell.AbstractShell):
    _rootShell: Shell = None

    def __init__(self, rootShell: Shell):
        self._rootShell = rootShell
        super().__init__()

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append("gitassets_command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self._rootShell.get_prompt_text(), "gitassets_command"])

    def asset_completion(self, text, line, begidx, endidx):
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        mapper = localstoragemapper(user)

        routines = self._rootShell.get_routines()
        routines.load()

        ret = []
        workingRoot = routines._root_config
        assets = workingRoot.GetWorkingAssets(mapper, True)
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

        args = self.parse_arguments(args)

        if len(args) == 0:
            print("No asset specified.")
            return

        routines = self._rootShell.get_routines()
        routines.load()
        routines.delete_asset(args[0])

    complete_create_asset = functools.partial(cmd2.Cmd.path_complete)

    def do_create(self, args):
        """Create a new asset at the given path

        Usage: create [path]

        arg path: The subpath to an asset to create.  It will be created whether the files/dir already exist, or not.
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            print("No path specified.")
            return

        routines = self._rootShell.get_routines()
        routines.load()
        self.do_coroutine(routines.create_asset_routine(args[0]))

    complete_enter = asset_completion

    def do_enter(self, args):
        """Enters a subshell for working with the given asset

        Usage: asset_shell [asset]

        arg asset: either the subpath or id of an asset in the current root.
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            print("No asset specified.")
            return

        routines = self._rootShell.get_routines()
        routines.load()
        asset = routines.get_asset(args[0])

        path = asset.GetSubmodule().path
        shell = GitAssetShell(routines.container.GetID(),routines.root.GetID(),asset.GetAsset().GetID())
        # shell = fiepipelib.shells.gitasset.Shell(asset, path, self._rootShell._container,
        #                                          self._rootShell._containerConfig, self._rootShell._GetRoot(),
        #                                          self._rootShell._GetConfig(), self._rootShell._localUser,
        #                                          self._rootShell._entity, self._rootShell._site)
        shell.cmdloop()

    def do_list(self, args):
        """
        Lists all assets currently available from the root.  Please keep in mind, some sub-assets may not be listed
        because their parents may not be checked out yet.

        Usage: list
        """
        routines = self._rootShell.get_routines()
        routines.load()
        assets = self.do_coroutine(routines.get_all_assets())
        for asset in assets:
            self.poutput(asset.GetSubmodule().path)