import abc
import os
import typing
from enum import Enum

from git import Repo, Submodule

from fiepipelib.automanager.data.localconfig import LegalEntityConfig
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fiepipelib.enum import get_worse_enum
from fiepipelib.git.routines.remote import get_commits_ahead, get_commits_behind
from fiepipelib.git.routines.repo import RepoExists, is_in_conflict
from fiepipelib.git.routines.submodules import CreateEmpty as CreateEmptySubmodule, Add as AddSubmodule, \
    CreateFromSubDirectory as CreateSubmoduleFromSubDirectory
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitstorage.data.git_asset import NewID as NewAssetID, is_valid_id
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines, GitLabFQDNGitAssetRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fieui.FeedbackUI import AbstractFeedbackUI


"""Structure is about 'static' paths.  What is 'static' and what is 'dynamic' is a bit amorphous.

A static path is a directory of file that 'must' or 'can' be structured in place and have routines and logic to it.

A dynamic path is a directory or file that has no known structure.

The fuzzy border between the two can be seen in a directory of maya (.mb) files.

The directory itself is probably static structure.  The files are fuzzy.  There can be assumed to be
some (N) number of files ending in *.mb extensions.  In a sense, those could be expressed as static structure based on what's on disk.
There might be a specific file, such as 'common.mb' which is always assumed to be there.  This file would most definitely
be a static structure.  But what about a bunch of *.tga files that are also in that directory?  They probably are not structure
as they're referenced inside the *.mb files.  But then again, they 'could' be treated as structure too if we wanted
to go that far. 

This is all to say: 'static structure' seems to be determined by: just how far and deep the developer wants to define it.
It's a choice.

In this package, we try to define minimal abstractions, which reflect the ultimate flexibility of the system to do whatever.
And also useful base-classes, which try to be a little more useful, in exchange for being a little more restrictive.
"""

BT = typing.TypeVar("BT", bound='AbstractPath')

class AbstractPath(typing.Generic[BT], abc.ABC):
    """A static path. Not a parent, not a child. Not dynamic. Not a subdirectory. Just an abtract static path. Might be leaf
    or a base or whatever. """

    @abc.abstractmethod
    def get_path(self) -> str:
        """Gets (calculates) the absolute path of this path.  The way this is done depends on the implementation."""
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self) -> bool:
        """Returns whether the static structure exists or not.
        Not recursive."""
        raise NotImplementedError()

    def get_base_static_path(self) -> BT:
        """Gets the base path in this static structure."""
        if isinstance(self, AbstractSubPath):
            parent = self.get_parent_path()
            return parent.get_base_static_path()
        else:
            return self

    @abc.abstractmethod
    async def automanager_create(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                 container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        """For auto-creation purposes.  Called by the auto-manager to create the static structure that should be
        created here.

        How this works is up to the implementation for the most part.  Guidelines follow however.

        The implementation should heed the configuration.  This is not an order to create structure.  It is an order to
        run the routine for creating structure.  If that routine says nothing shouldbe created becasue it's not configured
        as such, then that's the correct behavior.  But the return needs to reflect that.

        The implementation should try to return NO_CHANGES whenever it can reliably do so.

        The implementation should try to return CANNOT_COMPLETE proactively to keep further nested automanager routines from running
        when there is something wrong with this structure.
        """
        raise NotImplementedError()


class AbstractDirPath(AbstractPath[BT], typing.Generic[BT], abc.ABC):
    """Extends AbstractPath with the minimum requirements of a path that is a directory.
    A mix-in."""

    @abc.abstractmethod
    def get_subpaths(self) -> typing.List[AbstractPath]:
        """Gets static directory entires."""
        raise NotImplementedError

    def all_children_exist(self) -> bool:
        for subpath in self.get_subpaths():
            isgood = subpath.exists()
            if not isgood:
                return isgood
        return True

    @abc.abstractmethod
    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        """Called by the automanager_create routine to creat just this structure.  Children are automatically called and results checked elsewhere."""
        raise NotImplementedError()

    async def automanager_create(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                 container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        result = AutoCreateResults.NO_CHANGES

        self_result = await self.automanager_create_self(feedback_ui, entity_config, container_config)
        if self_result == AutoCreateResults.CANNOT_COMPLETE:
            await feedback_ui.error("Could not complete creation.  Canceling creation of children.")
            return self_result
        for subpath in self.get_subpaths():
            subpath_result = await subpath.automanager_create(feedback_ui, entity_config, container_config)
            get_worse_enum(result, subpath_result)
        return result


DT = typing.TypeVar("DT", bound=AbstractDirPath)


class AbstractSubPath(AbstractPath[BT], typing.Generic[BT, DT], abc.ABC):
    """Extends an AbstractPath with parts neccesary to act as a sub-path of a parent path.
    A mix-in."""

    _parent_path: DT = None

    def get_parent_path(self) -> DT:
        """The parent path to this sub-path"""
        return self._parent_path

    def __init__(self, parent_path: DT):
        self._parent_path = parent_path


# might kill these types... or move them to automanager?

class AutoManageResults(Enum):
    # order is important.  We're using a > to deal with reporting recursive status.
    CLEAN = 1  # all up to date with no dirty assets
    DIRTY = 2  # some dirty assets seemingly due to work-in-progress.
    UNPUBLISHED_COMMITS = 3  # some assets have unpublished commits and therefore, it's not safe to pull their parents.
    DIRTY_AND_UNPUBLISHED_COMMITS = 4  # some assets have unpublished commits but also, are dirty.
    PENDING = 5  # we won't know until we run parts of auto-update again.  This isn't an error though.  It's just a eventual convergence issue.
    CANNOT_COMPLETE = 6  # an error has occurred which negates the ability to continue the automanaging and requires user-intervention.


class AutoCreateResults(Enum):
    NO_CHANGES = 1  # no changes were needed to (re)create this structure.
    CHANGES_MADE = 2  # changes were made to (re)create this structure.
    CANNOT_COMPLETE = 3  # cannot (re)create this structure.


class AbstractGitStorageBasePath(AbstractDirPath[BT], typing.Generic[BT], abc.ABC):
    """A base path, which is based on a git storage type.  Either a root or asset."""

    _gitlab_server_name: str = None

    def get_gitlab_server_name(self):
        """The (local) name of the gitlab server this basepath should use for remote operations."""
        return self._gitlab_server_name

    def __init__(self, gitlab_server_name: str):
        self._gitlab_server_name = gitlab_server_name

    def get_sub_basepaths_recursive(self) -> typing.List["AbstractAssetBasePath"]:
        """A recursive version of get sub basepaths"""
        ret = []
        children = self.get_sub_basepaths()
        ret.extend(children)
        for child in children:
            ret.extend(child.get_sub_basepaths_recursive())
        return ret

    @abc.abstractmethod
    def get_sub_basepaths(self) -> typing.List["AbstractAssetBasePath"]:
        """Returns a list of AbstratAssetBasePaths that can be reached from inside this GitStorage Base Path.
        Not recursive into further BasePaths.  But yes, recursive through this entire static structure and
        also any dynamically generate-able BasePaths reachable from this static structure.
        e.g. yes, individual named character asset basepaths from within a static 'characters' directory.
        """
        raise NotImplementedError()

    def exists(self, recursive=True) -> bool:
        path = self.get_path()
        if not os.path.exists(path):
            return False
        if not RepoExists(path):
            return False
        return True

    def get_root_base_path(self) -> 'AbstractRootBasePath':
        base = self.get_base_static_path()
        if isinstance(base, AbstractRootBasePath):
            return base
        elif isinstance(base, AbstractAssetBasePath):
            return base.get_root_base_path()
        else:
            raise AssertionError("A git asset should never have a base that's not a git asset or git root.")

    @abc.abstractmethod
    def get_fqdn(self) -> str:
        """Gets the FQDN of this base"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_container_id(self) -> str:
        """Gets the container id of this base"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_root_id(self) -> str:
        """Gets the root id of this base"""
        raise NotImplementedError()

    def remote_is_ahead(self) -> bool:
        """return true or false if the remote is ahead of the local worktree or not"""
        repo = Repo(self.get_path())
        remote_commmits_ahead = get_commits_ahead(repo, "master", self.get_gitlab_server_name())
        return len(remote_commmits_ahead) > 0

    def remote_is_behind(self) -> bool:
        """returns true or false if the remote is behind the local worktree or not"""
        repo = Repo(self.get_path())
        remote_commmits_behind = get_commits_behind(repo, "master", self.get_gitlab_server_name())
        return len(remote_commmits_behind) > 0

    def is_conflicted(self) -> bool:
        repo = Repo(self.get_path())
        return is_in_conflict(repo)

    def is_detached(self) -> bool:
        """return true or false if the worktree is detached from the head or not"""
        repo = Repo(self.get_path())
        return repo.head.is_detached

    def is_checked_out(self) -> bool:
        """returns true of false if the worktree is checked out or not"""
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

    def is_dirty(self, consider_index: bool, consider_working_tree: bool, consider_untracked_files: bool,
                 consider_submodule_changes: bool):
        """Returns true or false based on whether the worktree is dirty as per the parameters
        :param consider_submodule_changes: whether to consider changes to submodules as making this tree 'dirty'
        :param consider_untracked_files: whether to consider the presence of untrack files as making thsi tree 'dirtt'
        :param consider_working_tree: whether to consider changes to the worktree as making this tree 'dirty'
        :param consider_index: whether to consider changes to the index as making this tree 'dirty'
        """
        repo = Repo(self.get_path())
        return repo.is_dirty(index=consider_index, working_tree=consider_working_tree,
                             untracked_files=consider_untracked_files, submodules=consider_submodule_changes)


class AbstractRootBasePath(AbstractGitStorageBasePath[BT], typing.Generic[BT], abc.ABC):
    """A basepath based on a git storage root"""
    _root_routines: GitRootRoutines = None

    def get_routines(self):
        """Gets GitRootRoutines"""
        return self._root_routines

    def get_fqdn(self) -> str:
        return self.get_routines().container.get_fqdn()

    def get_container_id(self) -> str:
        return self.get_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_routines().root.GetID()

    def __init__(self, gitlab_server_name: str, routines: GitRootRoutines):
        self._root_routines = routines
        super().__init__(gitlab_server_name)

    def get_path(self) -> str:
        return self._root_routines.get_local_repo_path()

    def get_gitlab_root_routines(self) -> GitLabFQDNGitRootRoutines:
        """Gets GitLabFQDNGitRootRooutines for this root."""
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        root_routines = self.get_routines()
        return GitLabFQDNGitRootRoutines(gitlab_server_routines, root_routines.root, root_routines.root_config)

    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        if not RepoExists(self.get_routines().get_local_repo_path()):
            await feedback_ui.error("Root isn't checked-out.  You may need to init it, or pull it from gitlab?")
            return AutoCreateResults.CANNOT_COMPLETE
        return AutoCreateResults.NO_CHANGES

    # TODO: rethink this?
    @abc.abstractmethod
    async def automanager_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                  container_config: ContainerAutomanagerConfigurationComponent):
        raise NotImplementedError()
        # entity_mode = entity_config.get_mode()
        # if entity_mode == LegalEntityMode.NONE:
        #     return
        # elif entity_mode == LegalEntityMode.USER_WORKSTATION:
        #     create_results = await self.auto_create_routine(feedback_ui)
        #     await feedback_ui.output("Running auto (re)creation.")
        #     if create_results == AutoCreateResults.CANNOT_COMPLETE:
        #         await feedback_ui.warn("The (re)creation of the structure cannot complete.")
        #         await feedback_ui.output("Canceling (re)configure and update until it's resolved.")
        #         return
        #     await feedback_ui.output("(re)creation result: " + create_results.name)
        #     await feedback_ui.output("Running auto (re)configuration.")
        #     configure_results = await self.auto_configure_routine(feedback_ui)
        #     if configure_results == AutoConfigurationResult.INTERVENTION_REQUIRED:
        #         await feedback_ui.warn(
        #             "The (re)configuration of the structure cannot complete and requires user intervention.")
        #         await feedback_ui.output("Canceling update until it's resolved.")
        #         return
        #     await feedback_ui.output("(re)configuration result: " + configure_results.name)
        #     await feedback_ui.output("Running auto update.")
        #     update_results = await self.auto_update_routine(feedback_ui)
        #     await feedback_ui.output("update result: " + update_results.name)


class AbstractAssetBasePath(AbstractGitStorageBasePath[BT], typing.Generic[BT]):
    """A base-path for a git storage asset."""
    _asset_routines: GitAssetRoutines

    def get_routines(self):
        """Gets the GitAssetRoutines"""
        return self._asset_routines

    def get_fqdn(self) -> str:
        return self.get_routines().container.get_fqdn()

    def get_container_id(self) -> str:
        return self.get_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_routines().root.GetID()

    def get_asset_id(self) -> str:
        """Gets the asset_id of the git asset at this base-path"""
        return self.get_asset_id()

    def __init__(self, gitlab_server_name: str, routines: GitAssetRoutines):
        self._asset_routines = routines
        super().__init__(gitlab_server_name)

    def get_path(self) -> str:
        return self._asset_routines.abs_path

    def get_gitlab_asset_routines(self) -> GitLabFQDNGitAssetRoutines:
        """Gets GitLabFQDNGitAssetRooutines for this root."""
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        asset_routines = self.get_routines()
        return GitLabFQDNGitAssetRoutines(gitlab_server_routines, asset_routines.working_asset,
                                          asset_routines.container.get_fqdn())

    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        if not RepoExists(self.get_routines().abs_path):
            await feedback_ui.error("Repository doesn't exist: " + self.get_routines().abs_path)
            return AutoCreateResults.CANNOT_COMPLETE
        # TODO: check that the module is checked-out first.
        # it's possible the path results in a parent repo rather than this module?  Need to check that.
        # also need to make sure it's not bare.
        return AutoCreateResults.NO_CHANGES


class StaticSubDir(AbstractSubPath[BT], AbstractDirPath[BT], typing.Generic[BT]):
    """A static subdirectory in the static structure.  Implements both SubPath and DirPath.
    Note, it's not a kind of submodule.  It is explicitly a normal subdirectory.
    Also, it's not just any subdirectory.  It's one that has pre-defined members rather than
    procedurally created members.  Though if you define no subpaths, it's just an un-managed directory."""

    _dirname: str = None
    _subpaths: typing.List[AbstractSubPath] = None

    def get_dirname(self) -> str:
        """The directory's name.  e.g. for the path c:\\foo\\bar this would return 'bar'"""
        return self._dirname

    def get_subpaths(self) -> typing.List[AbstractSubPath]:
        return self._subpaths.copy()

    def __init__(self, dirname: str, parent_path: AbstractDirPath):
        self._subpaths = []
        self._dirname = dirname
        super().__init__(parent_path)

    def add_subpath(self, subpath: AbstractSubPath):
        """Adds the given static SubPath to this directory."""
        subpath._parent_path = self
        self._subpaths.append(subpath)

    def get_path(self) -> str:
        return os.path.join(self.get_parent_path().get_path(), self._dirname)

    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        if self.exists():
            return AutoCreateResults.NO_CHANGES
        else:
            path = self.get_path()
            os.makedirs(path, exist_ok=True)
            # in theory, we don't need to add a directory on its own to git.  perhaps?
            # base_path = self.get_base_static_path()
            # assert isinstance(base_path, AbstractGitStorageBasePath)
            # repo = git.Repo(base_path.get_path())
            # repo.index.add([self.get_path()])
            return AutoCreateResults.CHANGES_MADE


class AssetsStaticSubDir(StaticSubDir[BT], typing.Generic[BT], abc.ABC):
    """A static subdirectory that contains N number of git storage assets.  A mix-in."""

    def get_submodules(self) -> typing.Dict[str, Submodule]:
        """Gets the contained assets as dictionary of git.Submodule objects where the directory name is the key."""
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

    def get_asset_routines_by_dirname(self, feedback_ui: AbstractFeedbackUI,
                                      dirname: str) -> GitAssetRoutines:
        """Gets an instance of GitAssetRoutines for a specific named sub-asset.
        Typically, you'll use get_submodules to get a named list, and then use the name to get the Routines.
        It's always possible someone deleted the asset in the interim, resulting in an exception throw."""
        submods = self.get_submodules()
        if dirname not in submods.keys():
            raise FileNotFoundError(dirname)
        submod = submods[dirname]
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        if not is_valid_id(submod.name):
            raise FileNotFoundError("Submod is not a valid Git Asset.  The name isn't a proper id: " + submod.name)
        return GitAssetRoutines(container_id=base_path.get_container_id(), root_id=base_path.get_root_id(),
                                asset_id=submod.name, feedback_ui=feedback_ui)

    def create_new_empty_asset(self, dirname: str):
        """Creates a new empty asset with a new id at the given directory name.
        Will throw an exception if the directory exists."""
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
        CreateEmptySubmodule(repo, relpath, asset_id, url)

    def add_from_existing_routine(self, dirname: str, asset_id: str):
        """Adds an pre-existing asset to this directory at the given dirname.  Requires the asset_id of
        that existing asset.  May throw if the directory already exists."""
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
        AddSubmodule(repo, asset_id, relpath, url)

    def subdir_to_new_asset_routine(self, dirname: str):
        """converts an existing subdirectory to a new asset with a new id.
        May throw if the directory doesn't already exist."""
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
        CreateSubmoduleFromSubDirectory(repo, relpath, asset_id, url=url)


TABP = typing.TypeVar("TABP", bound=AbstractAssetBasePath)


class GenericAssetBasePathsSubDir(AssetsStaticSubDir[BT], typing.Generic[BT, TABP], abc.ABC):
    """Convenience class for a subdir of assets of a particular type."""

    @abc.abstractmethod
    def get_asset_basepath_by_dirname(self, dirname: str, feedback_ui: AbstractFeedbackUI) -> TABP:
        """Create and return an appropriate AssetBasePath for the given dirname"""
        raise NotImplementedError()

    def get_asset_basepaths(self, feedback_ui: AbstractFeedbackUI) -> typing.List[TABP]:
        """Returns a list of AssetBasePaths for submodules that have been checked out."""
        ret = []
        submods = self.get_submodules()
        for dirname in submods.keys():
            submod = submods[dirname]
            # only return a basepath if it's been checked out.
            if submod.module_exists():
                ret.append(self.get_asset_basepath_by_dirname(dirname, feedback_ui))
        return ret
