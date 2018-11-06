import os
import os.path
import pathlib
import shlex
import typing

import git

from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager, \
    LocalContainerConfiguration
from fiepipelib.container.shared.data.container import LocalContainerManager, Container
from fiepipelib.git.routines.ignore import CheckCreateIgnore
from fiepipelib.git.routines.lfs import InstallLFSRepo
from fiepipelib.git.routines.repo import RepoExists, InitWorkingTreeRoot, DeleteLocalRepo
from fiepipelib.git.routines.submodules import Remove as RemoveSubmodule, CanCreateSubmodule, CreateFromSubDirectory
from fiepipelib.gitstorage.data.git_asset import NewID as NewAssetID
from fiepipelib.gitstorage.data.git_root import SharedGitRootsComponent, GitRoot
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfigurationsComponent, LocalRootConfiguration
from fiepipelib.gitstorage.data.localstoragemapper import localstoragemapper
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.routines.gitrepo import GitRepoRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.storage.localvolume import localvolume
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseQuestionUI import AbstractModalTrueFalseQuestionUI


class GitRootRoutines(GitRepoRoutines):
    _container_id: str = None
    _root_id: str = None
    _feedback_ui: AbstractFeedbackUI = None
    _true_false_question_ui: AbstractModalTrueFalseQuestionUI

    def __init__(self, container_id: str, root_id: str, feedback_ui: AbstractFeedbackUI,
                 true_false_question_ui: AbstractModalTrueFalseQuestionUI):
        self._container_id = container_id
        self._root_id = root_id
        self._feedback_ui = feedback_ui
        self._true_false_question_ui = true_false_question_ui

    def load(self):
        plat = get_local_platform_routines()
        self._user = LocalUserRoutines(plat)
        container_manager = LocalContainerManager(self._user)
        self._container = container_manager.GetByID(self._container_id)[0]
        container_configuration_manager = LocalContainerConfigurationManager(self._user)
        self._container_config = container_configuration_manager.GetByID(self._container_id)[0]
        self._roots_component = SharedGitRootsComponent(self._container)
        self._roots_component.Load()
        self._root = self._roots_component.get_by_id(self._root_id)
        self._roots_configuration_component = LocalRootConfigurationsComponent(self._container_config)
        self._roots_configuration_component.Load()
        self._root_config = self._roots_configuration_component.get_by_id(self._root_id)

    _user: LocalUserRoutines
    _container: Container
    _container_config: LocalContainerConfiguration
    _roots_component: SharedGitRootsComponent
    _roots_configuration_component: LocalRootConfigurationsComponent
    _root: GitRoot
    _root_config = LocalRootConfiguration

    def check_create_change_dir(self):
        mapper = localstoragemapper(self._user)
        dir = self._root_config.GetWorkingPath(mapper)
        if not os.path.exists(dir):
            os.makedirs(dir)
        elif not os.path.isdir(dir):
            raise NotADirectoryError(dir)
        os.chdir(dir)

    def get_local_repo_path(self) -> str:
        mapper = localstoragemapper(self._user)
        dir = self._root_config.GetWorkingPath(mapper)
        if os.path.exists(dir):
            if os.path.isdir(dir):
                os.chdir(dir)
        return dir

    def get_local_repo(self) -> git.Repo:
        """
        Gets the local repository if it exists.  Throws variously if there is a problem.  Calls 'is_dirty' internally.
        """
        mapper = localstoragemapper(self._user)
        rep = self._root_config.GetRepo(mapper)
        if not os.path.exists(rep.working_tree_dir):
            raise FileNotFoundError(rep.working_tree_dir)
        if not os.path.isdir(rep.working_tree_dir):
            raise NotADirectoryError(rep.working_tree_dir)
        return rep

    def get_repo(self) -> git.Repo:
        return self.get_local_repo()

    async def print_status_routine(self):
        existsText = "absent"
        statusText = "---"
        if RepoExists(self.get_local_repo_path()):
            existsText = "exists"
            rep = self.get_local_repo()
            if rep.is_dirty(untracked_files=True):
                statusText = "dirty"
            else:
                statusText = "clean"
        await self._feedback_ui.output(
            "root: {0} - {1} - {2} - {3}".format(self.get_local_repo_path(), root.GetID(), existsText, statusText))

    async def print_workingasset_status_routine(self, working_asset: GitWorkingAsset):
        existsText = "absent"
        statusText = "---"
        if working_asset.GetSubmodule().module_exists():
            existsText = "exists"
            rep = working_asset.GetSubmodule().module()
            assert isinstance(rep, git.Repo)
            if rep.is_dirty(untracked_files=True):
                statusText = "dirty"
            else:
                statusText = "clean"
        await self._feedback_ui.output(
            "asset: {0} - {1} - {2} - {3}".format(working_asset.GetSubmodule().path, working_asset.GetAsset().GetID(),
                                                  existsText,
                                                  statusText))

    async def print_status_recursive_routine(self):
        mapper = localstoragemapper(self._user)
        assets = self._root_config.GetWorkingAssets(mapper, True)
        await self.print_status_routine()
        for asset in assets:
            await self.print_workingasset_status_routine(asset)

    async def init_new(self):
        mapper = localstoragemapper(self._user)
        dir = self._root_config.GetWorkingPath(mapper)

        if RepoExists(dir):
            await self._feedback_ui.error("Already exists.")
            return

        await self._feedback_ui.output("Initializing Repo.")
        repo = InitWorkingTreeRoot(dir)
        await self._feedback_ui.output("Installing LFS to Repo.")
        InstallLFSRepo(repo)
        await self._feedback_ui.output("Setting up .gitignore")
        CheckCreateIgnore(repo)
        await self._feedback_ui.output("Commiting to head")
        repo.git.commit(m="Initial commit.")
        os.chdir(dir)
        return

    async def init_new_split(self, backingVolume: localvolume):
        """Initializes a brand new repository for the root with an empty working tree and a repository on a
        specified backing store.  See init_new for other details.

        Usage: init_new_split [volume]

        arg volume: the name of a mounted backing store to use for the split repository
        """

        mapper = localstoragemapper(self._user)

        await self._feedback_ui.output(
            "Creating repository on backing volume: " + backingVolume.GetName() + " " + backingVolume.GetPath())
        backingRep = self._root.CreateRepositoryOnBackingVolume(backingVolume)

        workingtreepath = self._root_config.GetWorkingPath(mapper)
        await self._feedback_ui.output(
            "Creating working tree on working volume: " + self._root.GetName() + " " + workingtreepath)
        backingRep.git.worktree("add", workingtreepath)
        workingRepo = git.Repo(workingtreepath)

        await self._feedback_ui.output("Installing LFS to Repo.")
        InstallLFSRepo(workingRepo)
        await self._feedback_ui.output("Setting up .gitignore")
        CheckCreateIgnore(workingRepo)
        await self._feedback_ui.output("Commiting to head")
        workingRepo.index.commit("Initial commit.")
        os.chdir(workingtreepath)

    async def checkout_worktree_from_backing_routine(self, backingVolume: localvolume):
        mapper = localstoragemapper(self._user)
        backingRep = self._root.GetRepositoryOnBackingVolume(backingVolume, create=False)

        workingtreepath = self._root_config.GetWorkingPath(mapper)
        await self._feedback_ui.output(
            "Creating working tree on working volume: " + self._root.GetName() + " " + workingtreepath)
        backingRep.git.worktree("add", workingtreepath)
        workingRepo = git.Repo(workingtreepath)

        os.chdir(workingtreepath)

    async def delete_worktree_routine(self):
        dir = self.get_local_repo_path()
        pardir = str(pathlib.Path(dir).parent)

        if not pathlib.Path(dir).exists():
            await self._feedback_ui.error("Doesn't exist.")
            return

        try:
            rep = self.get_local_repo()
        except git.InvalidGitRepositoryError:
            await self._feedback_ui.output("Invalid git repository.  Deleting contents of folder.")
            os.chdir(pardir)
            DeleteLocalRepo(dir)
            if pathlib.Path(dir).exists():
                await self._feedback_ui.error("Not fully deleted.")
            return

        if not rep.has_separate_working_tree():
            reply = await self._true_false_question_ui.execute(
                "The repository is inside the worktree and it will be deleted too.  Are you sure?")
            if reply == False:
                await self._feedback_ui.output("Aboriting.")
                return

        if rep.is_dirty():
            reply = await self._true_false_question_ui.execute(
                "The root is dirty and probably has uncommited changes.  Are you sure?")
            if reply == False:
                await self._feedback_ui.output("Aboriting.")
                return

        dir = rep.working_dir
        rep.close()
        os.chdir(pardir)
        DeleteLocalRepo(dir)

        if pathlib.Path(dir).exists():
            await self._feedback_ui.error("Not fully deleted.")

    async def get_all_assets(self, recursive=True) -> typing.List[GitWorkingAsset]:
        mapper = localstoragemapper(self._user)
        try:
            assets = self._root_config.GetWorkingAssets(mapper, recursive)
        except git.InvalidGitRepositoryError:
            await self._feedback_ui.error("Invalid git repository.  Did you init or pull the root?")
            raise
        return assets

    def get_asset(self, pathorid: str) -> GitWorkingAsset:
        """Returns a workingasset for a path or id from this root, if possible.
        """
        mapper = localstoragemapper(self._user)
        assets = self._root_config.GetWorkingAssets(mapper, True)
        work_tree_dir = self.get_local_repo().working_tree_dir
        for asset in assets:

            id = asset.GetAsset().GetID()
            if id.lower() == pathorid.lower():
                return asset

            relpath = os.path.relpath(asset.GetSubmodule().abspath,work_tree_dir)
            norm_relpath = os.path.normpath(relpath)
            norm_pathorid = os.path.normpath(pathorid)
            if norm_relpath == norm_pathorid:
                return asset

            #path = asset.GetSubmodule().path
            #norm_path = os.path.normpath(path)
            #if norm_path == norm_pathorid:
            #    return asset

        raise KeyError("Asset not found: " + pathorid)

    def get_asset_routines(self, pathorid: str) -> GitAssetRoutines:
        working_asset = self.get_asset(pathorid)
        return GitAssetRoutines(self._container_id, self._root_id, working_asset.GetAsset().GetID(), self._feedback_ui)

    def delete_asset(self, pathorid: str):
        workingAsset = self.get_asset(pathorid)
        rootRepo = self.get_local_repo()
        RemoveSubmodule(rootRepo, workingAsset.GetAsset().GetID())

    async def create_asset_routine(self, subpath: str):
        """Create a new asset at the given path

        Usage: create [path]

        arg path: The subpath to an asset to create.  It will be created whether the files/dir already exist, or not.
        """
        mapper = localstoragemapper(self._user)
        rootPath = os.path.abspath(self._root_config.GetWorkingPath(mapper))

        if os.path.isabs(subpath):
            if not subpath.startswith(rootPath):
                await self._feedback_ui.error("Absolute path isn't inside root path: " + subpath)
                return
            else:
                subpath = os.path.relpath(subpath, rootPath)
        # subpath is now certainly a relative path

        rep = self.get_local_repo()

        (creationRepo, creationSubPath) = CanCreateSubmodule(rep, subpath)

        if creationRepo is None:
            await self._feedback_ui.error("Cannot create asset at the given path.")
            await self._feedback_ui.error(
                "It might exist already.  Or it might be in a submodule that's not currently checked out.")
            return

        newid = NewAssetID()
        await self._feedback_ui.output("Creating new submodule for asset.")
        CreateFromSubDirectory(creationRepo, creationSubPath, newid, url=newid + ".git")

    async def commit_all_recursive(self, log_message: str):
        repo = self.get_repo()
        can_commit, reason = self.can_commit()
        if not can_commit:
            raise git.RepositoryDirtyError(repo=repo,message="root dirty: " + reason)
        all_assets = await self.get_all_assets(recursive=False)
        for asset in all_assets:
            asset_routines = GitAssetRoutines(self._container_id, self._root_id, asset.GetAsset().GetID(),
                                              self._feedback_ui)
            asset_routines.load()
            await asset_routines.commit_recursive(log_message)

        self.add_submodule_versions()
        if repo.is_dirty():
            repo.git.commit("-m", shlex.quote(log_message))

    def is_index_dirty(self) -> bool:
        repo = self.get_local_repo()
        return repo.is_dirty(index=True, working_tree=False, untracked_files=False, submodules=False)

    def is_worktree_dirty(self) -> bool:
        repo = self.get_local_repo()
        return repo.is_dirty(index=True, working_tree=False, untracked_files=False, submodules=False)

    def can_commit(self) -> (bool, str):
        repo = self.get_local_repo()

        dirty_index = repo.is_dirty(index=True, working_tree=False, untracked_files=False, submodules=False)

        dirty_worktree = repo.is_dirty(index=False, working_tree=True, untracked_files=False, submodules=False)

        if dirty_worktree:
            return False, "Dirty WorkTree"

        untracked_files = repo.is_dirty(index=False, working_tree=False, untracked_files=True, submodules=False)

        if untracked_files:
            return False, "Untracked Files"

        return True, "OK"

        #return (not repo.is_dirty(index=False, working_tree=True, untracked_files=True, submodules=True))
        # has_untracked = self.has_untracked()
        # index_dirty = self.is_index_dirty()
        # worktree_dirty = self.is_worktree_dirty()

        # if has_untracked:
        #     return False
        #
        # if worktree_dirty:
        #     return False

    @property
    def container(self):
        return self._container

    @property
    def root(self):
        return self._root

    @property
    def root_config(self):
        return self._root_config
