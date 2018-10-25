import json
import os
import os.path
import shlex
import typing

import git

from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager, \
    LocalContainerConfiguration
from fiepipelib.container.shared.data.container import LocalContainerManager, Container
from fiepipelib.gitstorage.data.git_asset import GitAsset
from fiepipelib.gitstorage.data.git_root import GitRoot, SharedGitRootsComponent
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfiguration, LocalRootConfigurationsComponent
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper
from fiepipelib.gitstorage.routines.gitrepo import GitRepoRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fieui.FeedbackUI import AbstractFeedbackUI


class GitAssetRoutines(GitRepoRoutines):
    _container_id: str = None
    _root_id: str = None
    _asset_id: str = None

    _feedback_ui: AbstractFeedbackUI = None

    def __init__(self, container_id: str, root_id: str, asset_id: str, feedback_ui: AbstractFeedbackUI):
        self._container_id = container_id
        self._root_id = root_id
        self._asset_id = asset_id
        self._feedback_ui = feedback_ui

    _user: LocalUserRoutines = None
    _container: Container = None
    _container_config: LocalContainerConfiguration = None
    _root: GitRoot
    _root_config: LocalRootConfiguration
    _asset: GitAsset
    _working_asset: GitWorkingAsset

    def get_repo(self) -> git.Repo:
        return self._working_asset.GetRepo()

    def load(self):
        plat = get_local_platform_routines()
        self._user = LocalUserRoutines(plat)
        container_manager = LocalContainerManager(self._user)
        self._container = container_manager.GetByID(self._container_id)[0]
        container_config_manager = LocalContainerConfigurationManager(self._user)
        self._container_config = container_config_manager.GetByID(self._container_id)[0]
        root_component = SharedGitRootsComponent(self._container)
        root_component.Load()
        self._root = root_component.get_by_id(self._root_id)
        root_config_component = LocalRootConfigurationsComponent(self._container_config)
        root_config_component.Load()
        self._root_config = root_config_component.get_by_id(self._root_id)
        self._asset = GitAsset(self._asset_id)
        mapper = localstoragemapper(self._user)
        for workingAsset in self._root_config.GetWorkingAssets(mapper, True):
            if workingAsset.GetAsset().GetID() == self._asset_id:
                self._working_asset = workingAsset

    @property
    def container(self):
        return self._container

    def get_sub_asset_routines(self) -> typing.List['GitAssetRoutines']:
        ret = []
        all_sub_assets = self._working_asset.GetSubWorkingAssets()
        for sub_asset in all_sub_assets:
            ret.append(
                GitAssetRoutines(self._container_id, self._root_id, sub_asset.GetAsset().GetID(), self._feedback_ui))
        return ret

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
                asset_routines.load()
                await asset_routines.deinit_branch()
            # then ourself
            await self.deinit()

    async def commit_recursive(self, log_message: str):
        if not self._working_asset.IsCheckedOut():
            return
        repo = self._working_asset.GetRepo()
        assert isinstance(repo, git.Repo)
        if len(repo.untracked_files) != 0:
            raise git.GitError(
                "Untracked files in asset: " + self._working_asset.GetSubmodule().abspath + ".  Cannot commit.")
        for sub_asset_routines in self.get_sub_asset_routines():
            sub_asset_routines.load()
            await sub_asset_routines.commit_recursive(log_message=log_message)
        if repo.is_dirty():
            await self._feedback_ui.feedback("Commiting: " + self._working_asset.GetSubmodule().path)
            log = repo.git.commit("-m" + shlex.quote(log_message))
            await self._feedback_ui.output(log)


    def get_config_names(self) -> typing.List[str]:
        """Returns names of config files in the asset.  No file extensions."""
        asset_path = self._working_asset.GetSubmodule().abspath
        configs_path = os.path.join(asset_path, "asset_configs")
        if not os.path.exists(configs_path):
            os.makedirs(configs_path, exist_ok=True)
            self._working_asset.GetRepo().index.add(["asset_configs"])
        contents = os.listdir(configs_path)
        config_filenames = []
        for entry in contents:
            if entry.endswith(".json"):
                config_filenames.append(entry)
        ret = []
        for config_filename in config_filenames:
            base, ext = os.path.splitext(config_filename)
            ret.append(base)
        return ret

    def has_config(self, name: str):
        names = self.get_config_names()
        if name in names:
            return True
        return False

    def get_config_data(self, name: str) -> typing.Dict:
        asset_path = self._working_asset.GetSubmodule().abspath
        configs_path = os.path.join(asset_path, "asset_configs")
        config_path = os.path.join(configs_path, name + ".json")
        f = open(config_path, 'r')
        data = json.load(f)
        f.close()
        return data

    def set_config_data(self, name: str, data: typing.Dict):
        asset_path = self._working_asset.GetSubmodule().abspath
        configs_path = os.path.join(asset_path, "asset_configs")
        config_path = os.path.join(configs_path, name + ".json")
        f = open(config_path, 'w')
        json.dump(data, f, sort_keys=True, indent=4)
        f.flush()
        f.close()

    def is_dirty_index(self) -> bool:
        repo = self._working_asset.GetRepo()
        return repo.is_dirty(working_tree=False, index=True, untracked_files=False)

    def is_dirty_worktree(self) -> bool:
        repo = self._working_asset.GetRepo()
        return repo.is_dirty(working_tree=True, index=False, untracked_files=False)

    def check_create_change_dir(self):
        submod = self._working_asset.GetSubmodule()
        dir = submod.abspath
        if not os.path.exists(dir):
            os.makedirs(dir)
        elif not os.path.isdir(dir):
            raise NotADirectoryError(dir)
        os.chdir(dir)

    def can_commit(self) -> (bool, str):
        if not self._working_asset.IsCheckedOut():
            return True, "OK: Not checked out"
        repo = self._working_asset.GetRepo()

        work_tree_dirty = repo.is_dirty(working_tree=True, index=False, untracked_files=False, submodules=False)

        if work_tree_dirty:
            return False, "Dirty WorkTree"

        # index_dirty = repo.is_dirty(working_tree=False, index=True ,untracked_files=False)

        untracked_files = self.has_untracked()

        if untracked_files:
            return False, "Untracked Files"

        modified_files = len(self.get_modified()) > 0

        if modified_files:
            return False, "Modified Files"

        return True, "OK"

    @property
    def working_asset(self):
        return self._working_asset
