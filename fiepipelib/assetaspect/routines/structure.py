import abc
import os
import typing

from git import InvalidGitRepositoryError, Repo, Submodule

from fiepipelib.git.routines.remote import get_commits_ahead, get_commits_behind
from fiepipelib.git.routines.repo import RepoExists
from fiepipelib.git.routines.submodules import CreateEmpty as CreateEmptySubmodule, Add as AddSubmodule, \
    CreateFromSubDirectory as CreateSubmoduleFromSubDirectory
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitstorage.data.git_asset import NewID as NewAssetID
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fieui.FeedbackUI import AbstractFeedbackUI


class AbstractPath(abc.ABC):

    @abc.abstractmethod
    def get_path(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def check_exists_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True) -> bool:
        """Returns whether the static structure exists or not.
        Should provide feedback as to why."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def create_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True):
        """Creates structure.  Should be forgiving of structure that already exists if possible.
        Should fail when neccesary."""
        raise NotImplementedError()

    def get_base_static_path(self) -> 'AbstractPath':
        if isinstance(self, AbstractSubPath):
            parent = self.get_parent_path()
            return parent.get_base_static_path()
        else:
            return self


class AbstractDirPath(AbstractPath, abc.ABC):

    @abc.abstractmethod
    def get_subpaths(self) -> typing.List[AbstractPath]:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI):
        """Creates just this DirPath.
          Should be forgiving of existing structure.
          Should fail if neccesary.
          Children are handled elsewhere."""
        raise NotImplementedError

    async def check_exists_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True) -> bool:
        path = self.get_path()
        if not os.path.exists(path):
            await feedback_ui.warn("Missing Dir: " + path)
            return False
        if not os.path.isdir(path):
            await feedback_ui.warn("Not a directory: " + path)
            return False
        if recursive:
            for subpath in self.get_subpaths():
                isgood = await subpath.check_exists_routine(feedback_ui, recursive)
                if not isgood:
                    return isgood
        return True

    async def create_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True):
        await self.create_self_routine(feedback_ui)
        if recursive:
            for subpath in self.get_subpaths():
                await subpath.create_routine(feedback_ui, recursive)


class AbstractSubPath(AbstractPath, abc.ABC):
    _parent_path: AbstractDirPath = None

    def get_parent_path(self) -> AbstractDirPath:
        return self._parent_path

    def __init__(self, parent_path: AbstractDirPath):
        self._parent_path = parent_path


class AbstractGitStorageBasePath(AbstractDirPath, abc.ABC):
    _subpaths: typing.List[AbstractSubPath] = None
    _gitlab_server_name: str = None

    def get_subpaths(self) -> typing.List[AbstractSubPath]:
        return self._subpaths.copy()

    def get_gitlab_server_name(self):
        return self._gitlab_server_name

    def __init__(self, gitlab_server_name: str):
        self._gitlab_server_name = gitlab_server_name
        self._subpaths = []

    def add_subpath(self, subpath: AbstractSubPath):
        subpath._parent_path = self
        self._subpaths.append(subpath)

    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI):
        # base paths just check that they exist and move on.
        # a git storage base-path also checks that it can made a valid repo
        path = self.get_path()
        if not os.path.exists(path):
            await feedback_ui.error("Base path doesn't exist: " + path)
            raise FileNotFoundError(path)
        if not RepoExists(path):
            await feedback_ui.error("Not a valid git repository: " + path)
            raise InvalidGitRepositoryError()

    @abc.abstractmethod
    def get_fqdn(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_container_id(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_root_id(self) -> str:
        raise NotImplementedError()

    def remote_is_ahead(self) -> bool:
        repo = Repo(self.get_path())
        remote_commmits_ahead = get_commits_ahead(repo, "master", self.get_gitlab_server_name())
        return len(remote_commmits_ahead) > 0

    def remote_is_behind(self) -> bool:
        repo = Repo(self.get_path())
        remote_commmits_behind = get_commits_behind(repo, "master", self.get_gitlab_server_name())
        return len(remote_commmits_behind) > 0

    def is_detached(self) -> bool:
        repo = Repo(self.get_path())
        return repo.head.is_detached

    def is_checked_out(self) -> bool:
        repo = Repo(self.get_path())
        # for a root, we check if we're bare.
        if repo.bare:
            return False

        # a de-init'd submodule is harder to detect.
        # the Repo will end up being set to the parent module.
        # but we can detect that by comparing paths.

        worktree_dir = repo.working_tree_dir
        path = self.get_path()

        if not os.path.samefile(worktree_dir, path):
            return False

        # if we get here, a valid repo with a worktree exists here.
        # So we assume it's checked out.

        return True

    def is_dirty(self):
        repo = Repo(self.get_path())
        return repo.is_dirty(index=True, working_tree=True, untracked_files=True, submodules=True)


class AbstractRootBasePath(AbstractGitStorageBasePath):
    _root_routines: GitRootRoutines = None

    def get_routines(self):
        return self._root_routines

    def get_fqdn(self) -> str:
        return self.get_routines().container.GetFQDN()

    def get_container_id(self) -> str:
        return self.get_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_routines().root.GetID()

    def __init__(self, gitlab_server_name: str, routines: GitRootRoutines):
        self._root_routines = routines
        super().__init__(gitlab_server_name)

    def get_path(self) -> str:
        return self._root_routines.get_local_repo_path()


class AbstractAssetBasePath(AbstractGitStorageBasePath):
    _asset_routines: GitAssetRoutines

    def get_routines(self):
        return self._asset_routines

    def get_fqdn(self) -> str:
        return self.get_routines().container.GetFQDN()

    def get_container_id(self) -> str:
        return self.get_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_routines().root.GetID()

    def get_asset_id(self) -> str:
        return self.get_asset_id()

    def __init__(self, gitlab_server_name: str, routines: GitAssetRoutines):
        self._asset_routines = routines
        super().__init__(gitlab_server_name)

    def get_path(self) -> str:
        return self._asset_routines.abs_path


class StaticSubDir(AbstractSubPath, AbstractDirPath):
    _dirname: str = None
    _subpaths: typing.List[AbstractSubPath] = None

    def get_dirname(self) -> str:
        return self._dirname

    def get_subpaths(self) -> typing.List[AbstractSubPath]:
        return self._subpaths.copy()

    def __init__(self, dirname: str, parent_path: AbstractDirPath):
        self._subpaths = []
        self._dirname = dirname
        super().__init__(parent_path)

    def add_subpath(self, subpath: AbstractSubPath):
        subpath._parent_path = self
        self._subpaths.append(subpath)

    def get_path(self) -> str:
        return os.path.join(self.get_parent_path().get_path(), self._dirname)

    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI):
        path = self.get_path()
        os.makedirs(path, exist_ok=True)


class AssetsStaticSubDir(StaticSubDir):
    """A static subdirectory that contains assets."""

    def get_submodules(self) -> typing.Dict[str, Submodule]:
        ret = {}
        repo = Repo(self.get_base_static_path().get_path())
        dir_path = self.get_path()
        submods = {}
        for submod in repo.submodules:
            assert isinstance(submod, Submodule)
            submod_parent_dir, submod_dirname = os.path.split(submod.abspath)
            if os.path.samefile(submod_parent_dir, dir_path):
                submods[submod_dirname] = submod
        return submods

    def get_asset_routines_by_dirname(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        submods = self.get_submodules()
        if dirname not in submods.keys():
            raise FileNotFoundError(dirname)
        submod = submods[dirname]
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        return GitAssetRoutines(container_id=base_path.get_container_id(), root_id=base_path.get_root_id(),
                                asset_id=submod.name, feedback_ui=feedback_ui)

    async def create_new_empty_asset(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        repo = Repo(base_path.get_path())
        dir_path = self.get_path()
        submod_abspath = os.path.join(dir_path, dirname)
        if os.path.exists(submod_abspath):
            raise FileExistsError("Path already exists: " + submod_abspath)
        asset_id = NewAssetID()
        relpath = os.path.relpath(submod_abspath, base_path.get_path())
        gitlab_server_routines = GitLabServerRoutines(base_path.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        await feedback_ui.output("Creating new empty submodule: " + submod_abspath)
        CreateEmptySubmodule(repo, relpath, asset_id, url)

    async def create_from_existing(self, feedback_ui: AbstractFeedbackUI, dirname: str, asset_id: str):
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        repo = Repo(base_path.get_path())
        dir_path = self.get_path()
        submod_abspath = os.path.join(dir_path, dirname)
        if os.path.exists(submod_abspath):
            raise FileExistsError("Path already exists: " + submod_abspath)
        relpath = os.path.relpath(submod_abspath, base_path.get_path())
        gitlab_server_routines = GitLabServerRoutines(base_path.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        await feedback_ui.output("Adding existing submodule: " + url + " at " + submod_abspath)
        AddSubmodule(repo, asset_id, relpath, url)

    async def subdir_to_new_asset(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        repo = Repo(base_path.get_path())
        dir_path = self.get_path()
        submod_abspath = os.path.join(dir_path, dirname)
        if not os.path.exists(submod_abspath):
            raise FileNotFoundError("Path doesn't exist: " + submod_abspath)
        asset_id = NewAssetID()
        relpath = os.path.relpath(submod_abspath, base_path.get_path())
        gitlab_server_routines = GitLabServerRoutines(base_path.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        await feedback_ui.output("Creating a new submodule from sub-directory at: " + submod_abspath)
        CreateSubmoduleFromSubDirectory(repo, relpath, asset_id, url=url)


class AbstractDesktopProjectRootBasePath(AbstractRootBasePath):

    def get_gitlab_root_routines(self) -> GitLabFQDNGitRootRoutines:
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        root_routines = self.get_routines()
        return GitLabFQDNGitRootRoutines(gitlab_server_routines,root_routines.root,root_routines.root_config)


    async def auto_update_routine(self, feedback_ui:AbstractFeedbackUI):
        """Root auto update behavior is as follows:

        auto_update all submodules/children first.

        If we're dirty(not_submodule) we tell the user to keep working and either commit or revert.  done.

        If we're ahead, we push.

        If we're behind or detached, we pull.

        If we're ahead and behind, we pull and check for success or failure.

            Upon failure, (due to conflict) we inform the user they'll need to merge. done.

            Upon success, done.


        """

        #TODO: update all children first.

        is_ahead = self.remote_is_behind()
        is_behind = self.remote_is_ahead()
        is_detached = self.is_detached()

        root_routines = self.get_routines()
        gitlab_root_routines = self.get_gitlab_root_routines()
        repo = root_routines.get_local_repo()

        is_dirty = repo.is_dirty(index=True,working_tree=True,untracked_files=True,submodules=False)

        unmerged_blobs = repo.index.unmerged_blobs()

        #checking for conflicts
        conflicted = False
        for path in unmerged_blobs:
            list_of_blobs = unmerged_blobs[path]
            for (stage, blob) in list_of_blobs:
                # Now we can check each stage to see whether there were any conflicts
                if stage != 0:
                    conflicted = True
        if conflicted:
            await feedback_ui.warn(self.get_path() + " is conflicted.")
            await feedback_ui.output("You will need to resolve conflicts or cancel the merge.")
            return


        #dirty disables auto upating until it's no longer dirty.
        if is_dirty:
            await feedback_ui.warn(self.get_path() + " is dirty.")
            await feedback_ui.output("Once you are done making changes, you'll want to either commit them, or revert them; to resume auto updating.")
            if is_behind:
                await feedback_ui.warn(self.get_path() + " has upstream changes.")
                await feedback_ui.output("You may wish to merge in the changes, or you could wait.")
            return

        #ahead and not behind or detached, is a push.
        if is_ahead and not (is_behind or is_detached):
            await gitlab_root_routines.push(feedback_ui)
            return

        #any pull could leave us conflicted.  If we are left conflicted, it's handled the next time we auto-update.

        #behind or detached, is a pull.
        if not is_ahead and (is_behind or is_detached):
            await gitlab_root_routines.pull(feedback_ui)
            return

        #ahead and behind is a pull.
        if is_ahead and (is_behind or is_detached):
            await gitlab_root_routines.pull(feedback_ui)
            return

        #most likely, we're up to date and clean.  with the exception of submodules, which may be even more up to date.
        return