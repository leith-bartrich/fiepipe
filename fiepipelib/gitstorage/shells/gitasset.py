import os
import os.path
import typing

import git

import fiepipelib.git.routines.repo
import fiepipelib.shells.AbstractShell
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.shells.vars.asset_id import AssetIDVarCommand
from fiepipelib.gitstorage.shells.vars.root_id import RootIDVarCommand


class Shell(fiepipelib.shells.AbstractShell.AbstractShell):
    _container_id_var: ContainerIDVariableCommand
    _root_id_var: RootIDVarCommand
    _asset_id_var: AssetIDVarCommand

    def __init__(self, container_id: str, root_id: str, asset_id: str):
        self._container_id_var = ContainerIDVariableCommand(container_id)
        self.add_variable_command(self._container_id_var, 'container', [], False)
        self._root_id_var = RootIDVarCommand(root_id)
        self.add_variable_command(self._root_id_var, 'root', [], False)
        self._asset_id_var = AssetIDVarCommand(asset_id)
        self.add_variable_command(self._asset_id_var, "asset", [], False)
        super(Shell, self).__init__()
        routines = self.get_routines()
        routines.load()
        routines._working_asset.GetSubmodule().abspath
        os.chdir(routines._working_asset.GetSubmodule().abspath)

    def get_routines(self) -> GitAssetRoutines:
        return GitAssetRoutines(self._container_id_var.get_value(), self._root_id_var.get_value(),
                                self._asset_id_var.get_value(), feedback_ui=self.get_feedback_ui())

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('gitasset')
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_routines()
        routines.load()
        fqdn = routines.container.GetFQDN()
        container_name = routines.container.GetShortName()
        subpath = routines._working_asset.GetSubmodule().path
        root_name = routines._root.GetName()
        return self.prompt_separator.join(['fiepipe', fqdn, container_name, root_name, subpath])

    # _localUser = None
    # _entity = None
    # _site = None
    # _container = None
    # _containerConfig = None
    # _workingAsset = None
    # _subpath = None
    # _root = None
    # _workingRoot = None
    #
    #
    # def __init__(self, workingasset, subpath, container, containerConfig, root, workingroot, localUser, entity, site):
    #     assert isinstance(container, fiepipelib.container.container)
    #     assert isinstance(containerConfig, fiepipelib.container.localconfiguration)
    #     assert isinstance(localUser, fiepipelib.localuser.localuser)
    #     assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
    #     assert isinstance(site,fiepipelib.abstractsite.abstractsite)
    #     assert isinstance(root, fiepipelib.gitstorage.root.root)
    #     assert isinstance(workingroot, fiepipelib.gitstorage.workingroot.workingroot)
    #     assert isinstance(workingasset, fiepipelib.gitstorage.workingasset.workingasset)
    #
    #     self._localUser = localUser
    #     self._entity = entity
    #     self._site = site
    #     self._container = container
    #     self._containerConfig = containerConfig
    #     self._workingAsset = workingasset
    #     self._subpath = subpath
    #     self._root = root
    #     self._workingRoot = workingroot
    #
    #
    #     super().__init__()
    #
    # os.chdir(self._workingAsset.GetSubmodule().abspath)

    # def do_checkout(self, args):
    #     """Checks out this asset from backing stores if available.
    #
    #     Usage: checkout
    #     """
    #     routines = self.get_routines()
    #     routines.load()
    #     self.do_coroutine(routines.do_checkout_routine())

    # def do_update(self, args):
    #     """Updates this asset from any mounted archive volumes.
    #
    #     Usage: update
    #     """
    #     mapper = fiepipelib.gitstorage.localstoragemapper.localstoragemapper(self._localUser)
    #     archiveVolumes = self._workingAsset.GetAsset().FindOnMountedArchiveVolumes(mapper)
    #     if len(archiveVolumes) == 0:
    #         print(self.colorize("Asset not found on any backing stores.","red"))
    #         return
    #
    #     for archiveVolume in archiveVolumes:
    #         fiepipelib.git.routines.submodules.ChangeURL(self._workingRoot.GetRepo(mapper), self._workingAsset.GetAsset().GetID(), self._workingAsset.GetAsset().GetPathForArchiveVolume(archiveVolume), revertGitModulesFile=True)
    #         fiepipelib.git.routines.submodules.Update(self._workingAsset.GetAsset().GetRepositoryOnArchiveVolume(archiveVolume), self._workingAsset.GetSubmodule(), False)
    #
    # def do_up(self, args):
    #     """Alias for update."""
    #     self.do_update(args)

    def do_status(self, args):
        """Prints git status of the asset.
        
        Usage: status
        """
        routines = self.get_routines()
        routines.load()
        submod = routines._working_asset.GetSubmodule()
        if not submod.module_exists():
            print(self.colorize("not checked out.", "yellow"))
            return
        rep = submod.module()
        assert isinstance(rep, git.Repo)
        rep.git.status()

    # def do_cull_dbhash_db(self):
    #     """Culls useless entries in the databasehash database for this asset.  A maintnance task.
    #
    #     Harmless to call it.  It might speed up some sqlite digital asset work.
    #
    #     Usage: cull_dbhash_db
    #     """
    #     man = fiepipelib.assetdata.databasehash.AssetDatabaseManager(
    #         self._workingAsset)
    #     man.Cull()
