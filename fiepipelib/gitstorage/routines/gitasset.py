import json
import os
import os.path
import shlex
import typing

import git

from fiepipelib.gitstorage.data.git_asset import GitAsset
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.routines.gitrepo import GitRepoRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines

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

    _root_routines: GitRootRoutines
    _asset: GitAsset
    _working_asset: GitWorkingAsset

    def load(self):
        self._root_routines = GitRootRoutines(self._container_id,self._root_id,self._feedback_ui)
        self._root_routines.load()
        self._asset = GitAsset(self._asset_id)
        submod = self._root_routines.get_repo().submodule(self._asset_id)
        self._working_asset = GitWorkingAsset(submod)

    @property
    def working_asset(self):
        return self._working_asset

    @property
    def relative_path(self):
        return os.path.relpath(self.abs_path, self.root_working_tree_path)

    @property
    def abs_path(self):
        return self._working_asset.GetSubmodule().abspath

    @property
    def root(self):
        return self._root_routines.root

    @property
    def root_config(self):
        return self._root_routines.root_config

    @property
    def root_working_tree_path(self):
        return self._root_routines.root_config.GetRepo(self._root_routines.mapper).working_tree_dir

    @property
    def container(self):
        return self._root_routines.container


    def get_repo(self) -> git.Repo:
        return self._working_asset.GetRepo()

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

    def is_init(self) -> bool:
        submod = self._working_asset.GetSubmodule()
        if not submod.exists():
            return False
        try:
            repo = submod.module()
            return True
        except git.InvalidGitRepositoryError:
            return False



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


class GitAssetInteractiveRoutines(GitAssetRoutines):



    pass


