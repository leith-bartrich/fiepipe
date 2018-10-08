import abc
import typing
from abc import ABC

import git

import fiepipelib.git.routines.submodules
from fiepipelib.git.routines.repo import RepoExists
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabGitStorageRoutines, GitLabServerRoutines
from fiepipelib.gitstorage.data.git_root import GitRoot
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfiguration
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper, get_local_storage_mapper
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.storage.localvolume import localvolume
from fieui.FeedbackUI import AbstractFeedbackUI


class GitLabGitRootRoutines(GitLabGitStorageRoutines, ABC):
    _root: GitRoot = None
    _root_config: LocalRootConfiguration = None

    def __init__(self, server_routines: GitLabServerRoutines, root: GitRoot, root_config: LocalRootConfiguration):
        self._root = root
        self._root_config = root_config
        super().__init__(server_routines)

    def get_remote_url(self) -> str:
        return self.get_server_routines().remote_path_for_gitroot(self.get_group_name(), self._root_config.GetID())

    def get_storage_mapper(self) -> localstoragemapper:
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        return localstoragemapper(user)

    def get_local_repo_path(self) -> str:
        mapper = self.get_storage_mapper()
        return self._root_config.GetWorkingPath(mapper)

    async def clone(self, feedback_ui: AbstractFeedbackUI):
        local_repo_path = self.get_local_repo_path()
        remote_url = self.get_remote_url()

        if RepoExists(local_repo_path):
            await feedback_ui.error("Repository already exists.  Cannot clone over it.")
            return
        else:
            await feedback_ui.output("Cloning from: " + remote_url + " -> " + local_repo_path)
            git.Repo.clone_from(remote_url, local_repo_path)

    async def clone_split(self, backing_vol: localvolume, feedback_ui: AbstractFeedbackUI):
        backing_vol_repo_path = self._root.GetPathForBackingVolume(backing_vol)
        local_worktree_path = self.get_local_repo_path()
        remote_url = self.get_remote_url()

        if RepoExists(backing_vol_repo_path):
            await feedback_ui.error(
                "Repository already exists.  Cannot clone over it.  Maybe just checkout a worktree instead?")
            return
        elif RepoExists(local_worktree_path):
            await feedback_ui.error("Worktree already exists.  Cannot checkout over it.")
            return
        else:
            # clone to backing vol with no worktree
            await feedback_ui.output("Initializing bare repository on backing volume: " + backing_vol_repo_path)
            git.Git(backing_vol_repo_path).clone("--bare", remote_url, backing_vol_repo_path)
            # add the worktree
            backing_repo = git.Repo(backing_vol_repo_path)
            await feedback_ui.output("Adding worktree: " + local_worktree_path)
            backing_repo.git.worktree("add", local_worktree_path)

    @abc.abstractmethod
    def get_all_asset_routines(self, recursive: bool) -> typing.List['GitLabGitAssetRoutines']:
        raise NotImplementedError()


class GitLabFQDNGitRootRoutines(GitLabGitRootRoutines):
    def get_all_asset_routines(self, recursive: bool) -> typing.List['GitLabFQDNGitAssetRoutines']:
        all_assets = self._root_config.GetWorkingAssets(get_local_storage_mapper(), recursive)
        ret = []
        for asset in all_assets:
            ret.append(GitLabFQDNGitAssetRoutines(self.get_server_routines(), asset, self._fqdn))
        return ret

    _fqdn: str = None

    def __init__(self, server_routines: GitLabServerRoutines, root: GitRoot, root_config: LocalRootConfiguration,
                 fqdn: str):
        self._fqdn = fqdn
        super().__init__(server_routines, root, root_config)

    def get_group_name(self) -> str:
        return "fiepipe." + self._fqdn


class GitLabGitAssetRoutines(GitLabGitStorageRoutines, ABC):
    _working_asset: GitWorkingAsset = None

    def __init__(self, server_routines: GitLabServerRoutines, working_asset: GitWorkingAsset):
        self._working_asset = working_asset
        super().__init__(server_routines)

    def get_remote_url(self) -> str:
        return self.get_server_routines().remote_path_for_gitasset(self.get_group_name(),
                                                                   self._working_asset.GetAsset().GetID())

    def get_local_repo_path(self) -> str:
        submod = self._working_asset.GetSubmodule()
        return submod.abspath

    @abc.abstractmethod
    def get_sub_asset_routines(self) -> typing.List['GitLabGitAssetRoutines']:
        raise NotImplementedError()

    async def init(self, feedback_ui: AbstractFeedbackUI):
        """Does an initial checkout of an asset that isn't currently checked out.
        Very likely leaves the asset in a 'detached head' state."""
        if not self._working_asset.IsCheckedOut():
            submod = self._working_asset.GetSubmodule()
            remote_url = self.get_remote_url()
            old_url = fiepipelib.git.routines.submodules.GetURL(submod.repo, submod.name)
            fiepipelib.git.routines.submodules.ChangeURL(submod.repo, submod.name, remote_url,
                                                         revertGitModulesFile=False)
            textout = submod.repo.git.submodule("update", "--init", submod.abspath)
            await feedback_ui.output(textout)
            fiepipelib.git.routines.submodules.ChangeURL(submod.repo, submod.name, old_url, revertGitModulesFile=False)
            # repo.git.submodule("init",submod.abspath)

    async def init_branch(self, feedback_ui: AbstractFeedbackUI):
        """recursive init from this asset through all its children.
        Like init, it likely leaves the assets in a 'detached head' state.
        """
        if not self._working_asset.IsCheckedOut():
            await self.init(feedback_ui=feedback_ui)
            for asset_routines in self.get_sub_asset_routines():
                await asset_routines.init_branch()

    async def deinit(self):
        """Un-checks out an asset that is currently checked out."""
        submod = self._working_asset.GetSubmodule()
        if submod.exists():
            repo = submod.repo
            assert isinstance(repo, git.Repo)
            repo.git.submodule("deinit", submod.abspath)

    async def deinit_branch(self):
        """Recursive de-init that de-inits children before parents."""
        submod = self._working_asset.GetSubmodule()
        if submod.exists():
            # children first!
            for asset_routines in self.get_sub_asset_routines():
                await asset_routines.deinit_branch()
            # then ourself
            await self.deinit()

    async def update(self, feedback_ui: AbstractFeedbackUI, latest=True, init=False):
        """Pulls and updates the worktree of an asset that is checked out to the latest commit on 'master'.

        Not recursive.

        Doesn't init assets
        that are not checked out unless init=True.

        if latest is true, the update is to the latest commit on the tracking branch.
        If latest is false, the update is to the commit that was checked out when the parent commit
        was made.

        latest = True is the latest and greatest.
        latest = False is the pedantically correct version that goes with the parent.

        init = True will automatically revert to a init to check out the module if it is not already.
        init = False will skip a submodule that isn't checked out.

        init = True and latest = True will do an init an then also an update to the latest.
        """

        if self._working_asset.IsCheckedOut():
            await self.pull(feedback_ui=feedback_ui)
        else:
            if init:
                await self.init(feedback_ui=feedback_ui)
            else:
                return

        if latest:
            textout = self._working_asset.GetRepo().git.checkout("master")
            await feedback_ui.output(textout)

    async def update_branch(self, feedback_ui: AbstractFeedbackUI, latest=True, init=False):
        """Recursive version of update that walks down the tree of checked out assets.
        :arg latest updates to submodule, rather than the commit that was checked out, when it was commited.
        :arg init checks out submodules that have not been checked out.  When false, it skips them instead.

        Often, submodules are updated more often than their parent (sub)modules.
        An updated submodule could break its parent.  It's a dependency issue to assume latest always.

        Conversely, you would find it hard to get updated submodules without being able to explicitly just call for
        the latest and greatest easily.

        latest = True and init = True
            gets you the latest and greatest of everything.
        latest = False and init = True
            gets you a consistent but complete tree as the last commit saw it.
        latest = True and init = False
            gets you the latest and greatest of what you already have.
        latest = False and init = False
            gets you a consistent version of what you already have, as the last commit saw it.

        """
        await self.update(feedback_ui=feedback_ui, latest=latest, init=init)
        for sub_asset_routines in self.get_sub_asset_routines():
            await sub_asset_routines.update_branch(feedback_ui=feedback_ui, latest=latest, init=init)

    async def push_branch(self, feedback_ui: AbstractFeedbackUI):
        # we skip un-init submods.
        if self._working_asset.IsCheckedOut():
            # children first.
            for sub_asset_routines in self.get_sub_asset_routines():
                await sub_asset_routines.push_branch(feedback_ui=feedback_ui)
            # then ourselves.
            await self.push(feedback_ui=feedback_ui)


class GitLabFQDNGitAssetRoutines(GitLabGitAssetRoutines):
    _fqdn: str = None

    def __init__(self, server_routines: GitLabServerRoutines, working_asset: GitWorkingAsset, fqdn: str):
        self._fqdn = fqdn
        super().__init__(server_routines, working_asset)

    def get_group_name(self) -> str:
        return "fiepipe." + self._fqdn

    def get_sub_asset_routines(self) -> typing.List[GitLabGitAssetRoutines]:
        sub_assets = self._working_asset.GetSubWorkingAssets()
        ret = []
        for asset in sub_assets:
            ret.append(GitLabFQDNGitAssetRoutines(self.get_server_routines(), asset, self._fqdn))
        return ret
