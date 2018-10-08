import functools
import typing

import cmd2

import fiepipelib.shells.AbstractShell
from fiepipelib.container.shells.container_id_var_command import ContainerIDVariableCommand
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitlabserver.data.gitlab_server import GitLabServerManager
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fiepipelib.gitstorage.shells.gitasset import Shell as GitAssetShell
from fiepipelib.gitstorage.shells.ui.log_message_input_ui import LogMessageInputUI
from fiepipelib.gitstorage.shells.vars.root_id import RootIDVarCommand
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.gitstorage.shells.gitroot_gitlab_server import Shell as GitLabGitRootShell
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

        gitlab_command = GitLabServerCommand(self)
        self.add_submenu(gitlab_command,"gitlab",['gl'])

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

    def do_commit(self, args):
        """Commits the changes in the asset tree and the root.

        Usage: commit
        """
        log_message_input_ui = LogMessageInputUI(self)
        log_message = self.do_coroutine(log_message_input_ui.execute("Log message"))
        routines = self.get_routines()
        routines.load()
        self.do_coroutine(routines.commit(log_message))


class GitLabServerCommand(fiepipelib.shells.AbstractShell.AbstractShell):

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(GitLabServerCommand, self).get_plugin_names_v1()
        ret.append("gitrooot_gitlabserver_command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self._rootShell.get_prompt_text(),"GitLab_server_command"])

    _rootShell: Shell = None

    def __init__(self, rootShell: Shell):
        self._rootShell = rootShell
        super().__init__()

    def complete_enter(self, text, line, begidx, endidx):
        user = LocalUserRoutines(get_local_platform_routines())
        man = GitLabServerManager(user)
        ret = []
        for server in man.GetAll():
            if server.get_name().startswith(text):
                ret.append(server.get_name())
        return ret

    def do_enter(self, args):
        """Enters a shell for working with this GitRoot to/from a GitLab server.
        Usage: enter [name]

        arg name:  The name of the GitLab server to use.
        """
        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No server name given.")
            return

        routines = self._rootShell.get_routines()
        routines.load()


        server_routines = GitLabServerRoutines(args[0])
        root_routines = GitLabFQDNGitRootRoutines(server_routines, routines.root, routines.root_config,
                                          routines.container.GetFQDN())

        shell = GitLabGitRootShell(root_routines)
        shell.cmdloop()


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

    def do_remove(self, args):
        """Removes (deletes) an asset from the root.

        WARNING: this is not just a local change.  You are actually removing the asset from the project.

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
        shell = GitAssetShell(routines.container.GetID(), routines.root.GetID(), asset.GetAsset().GetID())
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

    def do_clear_from_worktree(self, args):
        """Removes (clears) the worktree for the given asset branch.
        The asset remains in the project for others, it simply clears it from the local worktree
        and can be checked-out again from appropriate sources (such as gitlab)

        The command is assumed to be recursive.

        Usage: clear_from_worktree [asset]

        arg asset:  The subpath or id of the asset from which to clear the branch.
        """
        args = self.parse_arguments(args)

        routines = self._rootShell.get_routines()
        routines.load()
        for arg in args:
            asset = routines.get_asset(arg)
            asset_routines = GitAssetRoutines(routines.container.GetID(), routines.root.GetID(), asset.GetAsset().GetID(),
                                              self.get_feedback_ui())
            asset_routines.load()
            self.do_coroutine(asset_routines.deinit_branch())
