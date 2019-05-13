import abc
import os
import typing
from enum import Enum

from git import Repo, Submodule

from fiepipelib.automanager.data.localconfig import LegalEntityConfig
from fiepipelib.automanager.routines.automanager import AutoManagerRoutines
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager
from fiepipelib.localuser.routines.localuser import get_local_user_routines
from fiepipelib.enum import get_worse_enum
from fiepipelib.git.routines.remote import get_commits_ahead, get_commits_behind, exists as remote_exists
from fiepipelib.git.routines.repo import RepoExists, is_in_conflict
from fiepipelib.git.routines.submodules import CreateEmpty as CreateEmptySubmodule, Add as AddSubmodule, \
    CreateFromSubDirectory as CreateSubmoduleFromSubDirectory, add_gitmodules_file
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitstorage.data.git_asset import NewID as NewAssetID, is_valid_id
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines, GitAssetInteractiveRoutines
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines, GitLabFQDNGitAssetRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fiepipelib.automanager.routines.automanager import AutoManagerRoutines

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
    or a base or whatever.

    Generic types BT

    BT: the base path's type - AbstractPath"""

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
        run the routine for creating structure.  If that routine says nothing should be created because it's not configured
        as such, then that's the correct behavior.  But the return needs to reflect that.

        The implementation should try to return NO_CHANGES whenever it can reliably do so.

        The implementation should try to return CANNOT_COMPLETE proactively to keep further nested automanager routines from running
        when there is something wrong with this structure.

        Generally speaking, git-add should be run by the implementation of this method when things are created.  But not haphazzardly.
        Keep in mind, that running git-add on a directory adds all content.  Which is dangerous.  But also, git-add of a
        directory is never necceesary.  Git tracks files, not directories.  So the rule is: git-add files here.  Don't git-add directories here.

        Also, there is no need to git-add everything here.  Just the static structure for creation should be added.
        Automanger should handle content managment elsewhere.
        """
        raise NotImplementedError()


class AbstractDirPath(AbstractPath[BT], typing.Generic[BT], abc.ABC):
    """Extends AbstractPath with the minimum requirements of a path that is a directory.
    A mix-in.

    Generics BT

    BT: the base path's type - AbstractPath"""

    @abc.abstractmethod
    def get_subpaths(self) -> "typing.List[AbstractSubPath[BT]]":
        """Gets static directory entires."""
        raise NotImplementedError

    def get_subpaths_recursive(self) -> typing.List[AbstractPath]:
        ret = []
        for subpath in self.get_subpaths():
            ret.append(subpath)
            if isinstance(subpath,AbstractDirPath):
                ret.extend(subpath.get_subpaths_recursive())
        return ret



    def all_children_exist(self) -> bool:
        for subpath in self.get_subpaths():
            isgood = subpath.exists()
            if not isgood:
                return isgood
        return True

    @abc.abstractmethod
    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        """Called by the automanager_create routine to create just this structure.  Children are automatically called and results checked elsewhere."""
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
    A mix-in.

    Generics BT, DT

    BT: the base path's type - AbstractPath
    DT: the parent path's type - AbstractDirPath"""

    _parent_path: DT = None

    def get_parent_path(self) -> DT:
        """The parent path to this sub-path"""
        return self._parent_path

    def __init__(self, parent_path: DT):
        self._parent_path = parent_path

    def get_name(self) -> str:
        parent_path = self._parent_path.get_path()
        self_path = self.get_path()
        return os.path.relpath(self_path,parent_path)

# might kill these types... or move them to automanager?

class AutoManageResults(Enum):
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
    """A base path, which is based on a git storage type.  Either a root or asset.

    Generics BT

    BT: Base path's type - AbstractPath"""

    @abc.abstractmethod
    def get_gitlab_server_name(self):
        """The (local) name of the gitlab server this basepath should use for remote operations."""
        raise NotImplementedError()

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
        remote_commits_ahead = get_commits_behind(repo, "master", self.get_gitlab_server_name())
        return len(remote_commits_ahead) > 0

    def remote_is_behind(self) -> bool:
        """returns true or false if the remote is behind the local worktree or not"""
        repo = Repo(self.get_path())
        local_commits_ahead = get_commits_ahead(repo, "master", self.get_gitlab_server_name())
        return len(local_commits_ahead) > 0

    def remote_exists(self) -> bool:
        repo = Repo(self.get_path())
        return remote_exists(repo,self.get_gitlab_server_name())


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

TARBP = typing.TypeVar("TARBP", bound= "AbstractRootBasePath")

class AbstractRootBasePath(AbstractGitStorageBasePath[TARBP], typing.Generic[TARBP], abc.ABC):
    """A basepath based on a git storage root

    Generics BT

    BT: base path's type: AbstractPath
    """
    _root_routines: GitRootRoutines = None

    def get_routines(self):
        """Gets GitRootRoutines"""
        return self._root_routines

    def get_fqdn(self) -> str:
        return self.get_routines().container.GetFQDN()

    def get_container_id(self) -> str:
        return self.get_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_routines().root.GetID()

    def __init__(self, routines: GitRootRoutines):
        self._root_routines = routines
        super().__init__()

    def get_path(self) -> str:
        return self._root_routines.get_local_repo_path()

    def get_gitlab_server_name(self):
        container_id = self.get_container_id()
        manager = LocalContainerConfigurationManager(get_local_user_routines())
        configs =  manager.GetByID(container_id)
        if len(configs) == 0:
            raise KeyError(container_id)
        config = configs[0]
        automanager_routines = AutoManagerRoutines(0.0)
        container_automan_config = automanager_routines.get_container_config(config)
        container_automan_config.Load()
        return container_automan_config.get_root_gitlab_server(self.get_root_id())

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

    @abc.abstractmethod
    async def automanager_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                  container_config: ContainerAutomanagerConfigurationComponent) -> AutoManageResults:
        raise NotImplementedError()

TAABP = typing.TypeVar("TAABP", bound="AbstractAssetBasePath")

class AbstractAssetBasePath(AbstractGitStorageBasePath[TAABP], typing.Generic[TAABP]):
    """A base-path for a git storage asset.

    Generics BT

    BT: base path's type - Abstract Path"""
    _asset_routines: GitAssetRoutines

    def get_asset_routines(self):
        """Gets the GitAssetRoutines"""
        return self._asset_routines

    def get_fqdn(self) -> str:
        return self.get_asset_routines().container.GetFQDN()

    def get_container_id(self) -> str:
        return self.get_asset_routines().container.GetID()

    def get_root_id(self) -> str:
        return self.get_asset_routines().root.GetID()

    def get_asset_id(self) -> str:
        """Gets the asset_id of the git asset at this base-path"""
        return self._asset_routines.working_asset.GetAsset().GetID()

    def __init__(self, routines: GitAssetRoutines):
        self._asset_routines = routines
        super().__init__()

    def get_path(self) -> str:
        return self._asset_routines.abs_path

    def get_gitlab_server_name(self):
        container_id = self.get_container_id()
        manager = LocalContainerConfigurationManager(get_local_user_routines())
        configs =  manager.GetByID(container_id)
        if len(configs) == 0:
            raise KeyError(container_id)
        config = configs[0]
        automanager_routines = AutoManagerRoutines(0.0)
        container_automan_config = automanager_routines.get_container_config(config)
        container_automan_config.Load()
        return container_automan_config.get_asset_gitlab_server(self.get_asset_id())


    def get_gitlab_asset_routines(self) -> GitLabFQDNGitAssetRoutines:
        """Gets GitLabFQDNGitAssetRooutines for this root."""
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        asset_routines = self.get_asset_routines()
        return GitLabFQDNGitAssetRoutines(gitlab_server_routines, asset_routines.working_asset,
                                          asset_routines.container.GetFQDN())

    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        routines = self.get_asset_routines()
        routines.load()
        if not RepoExists(routines.abs_path):
            await feedback_ui.error("Repository doesn't exist: " + routines.abs_path)
            return AutoCreateResults.CANNOT_COMPLETE
        # TODO: check that the module is checked-out first.
        # it's possible the path results in a parent repo rather than this module?  Need to check that.
        # also need to make sure it's not bare.
        return AutoCreateResults.NO_CHANGES


class StaticSubDir(AbstractSubPath[BT,DT], AbstractDirPath[BT], typing.Generic[BT, DT]):
    """A static subdirectory in the static structure.  Implements both SubPath and DirPath.
    Note, it's not a kind of submodule.  It is explicitly a normal subdirectory.
    Also, it's not just any subdirectory.  It's one that has pre-defined members rather than
    procedurally created members.  Though if you define no subpaths, it's just an un-managed directory.

    Generic types: BT,DT

    BT: the base path's type - AbstractPath
    DT: the parent's type - AbstractDirPath"""

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

    def exists(self) -> bool:
        path = self.get_path()
        if not os.path.exists(path):
            return False
        if not os.path.isdir(path):
            raise NotADirectoryError()
        return True

    async def automanager_create_self(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                      container_config: ContainerAutomanagerConfigurationComponent) -> 'AutoCreateResults':
        if self.exists():
            return AutoCreateResults.NO_CHANGES
        else:
            path = self.get_path()
            os.makedirs(path, exist_ok=True)
            #git doesn't track empty directories (or directories at all really) so no need to add it.
            return AutoCreateResults.CHANGES_MADE


class AssetsStaticSubDir(StaticSubDir[BT,DT], typing.Generic[BT,DT], abc.ABC):
    """A static subdirectory that contains N number of git storage assets.  A mix-in.

    Generics BT,DT

    BT: base path's type: AbstractPath
    DT: parent dir's type: AbstractDirPath"""

    def get_submodules(self) -> typing.Dict[str, Submodule]:
        """Gets the contained assets as dictionary of git.Submodule objects where the directory name is the key."""
        ret = {}
        repo = Repo(self.get_base_static_path().get_path())
        dir_path = self.get_path()
        submods = {}
        for submod in repo.submodules:
            assert isinstance(submod, Submodule)
            submod_parent_dir, submod_dirname = os.path.split(submod.abspath)
            #we compare normpaths here because samepath actually checks, files, not paths.
            if os.path.normpath(submod_parent_dir) == os.path.normpath(dir_path):
                submods[submod_dirname] = submod
        return submods

    def get_ids_by_dirname(self, dirname:str) -> (str,str,str):
        """Returns container_id, root_id, and asset_id for the given dirname"""
        submods = self.get_submodules()
        if dirname not in submods.keys():
            raise FileNotFoundError(dirname)
        submod = submods[dirname]
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        if not is_valid_id(submod.name):
            raise FileNotFoundError("Submod is not a valid Git Asset.  The name isn't a proper id: " + submod.name)
        return base_path.get_container_id(),base_path.get_root_id(),submod.name

    def get_asset_routines_by_dirname(self, dirname: str) -> GitAssetRoutines:
        """Gets an instance of GitAssetRoutines for a specific named sub-asset.
        """
        container_id, root_id, asset_id = self.get_ids_by_dirname(dirname)
        return GitAssetRoutines(container_id=container_id, root_id=root_id,
                                asset_id=asset_id)

    def get_asset_interactive_routines_by_dirname(self, dirname: str) -> GitAssetInteractiveRoutines:
        """Gets an instance of GitAssetInteractiveRoutines for a specific named sub-asset.
        """
        container_id, root_id, asset_id = self.get_ids_by_dirname(dirname)
        return GitAssetInteractiveRoutines(container_id=container_id, root_id=root_id,
                                asset_id=asset_id)

    def get_asset_gitlab_routines_by_dirname(self, dirname:str) -> GitLabFQDNGitAssetRoutines:
        base_path = self.get_base_static_path()
        assert isinstance(base_path,AbstractGitStorageBasePath)
        gitlab_server_name = self.get_gitlab_server_name()
        asset_routines = self.get_asset_routines_by_dirname(dirname)
        asset_routines.load()
        server_routines = GitLabServerRoutines(gitlab_server_name)
        asset_server_routines = GitLabFQDNGitAssetRoutines(server_routines,asset_routines.working_asset,base_path.get_fqdn())
        return asset_server_routines


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
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        CreateEmptySubmodule(repo, relpath, asset_id, url)
        add_gitmodules_file(repo)

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
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        AddSubmodule(repo, asset_id, relpath, url)
        add_gitmodules_file(repo)

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
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        groupname = gitlab_server_routines.group_name_from_fqdn(base_path.get_fqdn())
        url = gitlab_server_routines.remote_path_for_gitasset(groupname, asset_id)
        CreateSubmoduleFromSubDirectory(repo, relpath, asset_id, url=url)
        add_gitmodules_file(repo)

    def get_gitlab_server_name(self) -> str:
        """Gets the gitlab server name for this set of assets to pull from.
        Default implementation gets it from this base path.  Override this to get it
        another way."""
        base_path = self.get_base_static_path()
        assert isinstance(base_path,AbstractGitStorageBasePath)
        gitlab_server_name = base_path.get_gitlab_server_name()
        return gitlab_server_name


    async def checkout_by_dirname_routine(self, dirname:str, feedback_ui:AbstractFeedbackUI):
        "Checks out the asset from gitlab."
        base_path = self.get_base_static_path()
        assert isinstance(base_path,AbstractGitStorageBasePath)
        base_repo_path = base_path.get_path()
        base_repo = Repo(base_repo_path)
        asset_server_routines = self.get_asset_gitlab_routines_by_dirname(dirname)
        asset_id = asset_server_routines.working_asset.GetAsset().GetID()
        await asset_server_routines.init_submodule_sub_routine(feedback_ui,asset_id,base_repo,"master")



TABP = typing.TypeVar("TABP", bound=AbstractAssetBasePath)


class GenericAssetBasePathsSubDir(AssetsStaticSubDir[BT,DT], typing.Generic[BT, DT, TABP], abc.ABC):
    """Convenience class for a subdir of assets of a particular type.

    Generics BT, DT, TABP

    BT: bast path's type: AbstractPath
    DT: parent dir's type: AbstractDirPath
    TABP: asset base path type: AbstractAssetBasePath"""

    @abc.abstractmethod
    def get_asset_basepath_by_dirname(self, dirname: str) -> TABP:
        """Create and return an appropriate AssetBasePath for the given dirname"""
        raise NotImplementedError()

    def get_asset_basepaths(self) -> typing.List[TABP]:
        """Returns a list of AssetBasePaths for submodules that have been checked out."""
        ret = []
        submods = self.get_submodules()
        for dirname in submods.keys():
            submod = submods[dirname]
            # only return a basepath if it's been checked out.
            if submod.module_exists():
                ret.append(self.get_asset_basepath_by_dirname(dirname))
        return ret

    async def autocreate_asset_by_dirname(self, dirname: str, feedback_ui:AbstractFeedbackUI):
        asset_base_path = self.get_asset_basepath_by_dirname(dirname)
        asset_routines = asset_base_path.get_asset_routines()
        asset_routines.load()
        automanager_routines = AutoManagerRoutines(0.0)
        entity_config = automanager_routines.get_legal_entitiy_config(asset_routines.container.GetFQDN())
        container_config = automanager_routines.get_container_config(asset_routines.container_config)
        await asset_base_path.automanager_create(feedback_ui,entity_config,container_config)
