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
from fiepipelib.gitstorage.routines.gitasset import GitAssetInteractiveRoutines
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines, GitLabFQDNGitAssetRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from enum import Enum
from fiepipelib.enum import get_worse_enum
from fiepipelib.assetaspect.routines.autoconf import AutoConfigurationResult


class AbstractPath(abc.ABC):
    """A static path. Not a parent, not a child. Not dynamic. Not a subdirectory. Just an abtract path. Might be leaf
    or a base or whatever. """

    @abc.abstractmethod
    def get_path(self) -> str:
        """Gets (calculates) the absolute path of this path.  The way this is done depends on the implementation."""
        raise NotImplementedError

    @abc.abstractmethod
    async def check_exists_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True) -> bool:
        """Returns whether the static structure exists or not.
        Should provide feedback as to why."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def create_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True) -> bool:
        """Creates structure.  Should be forgiving of structure that already exists if possible.
        Should fail when neccesary.
        Should provide feeedback as to failure.

        Returns true if created or okay.  Returns false if creation failed."""
        raise NotImplementedError()

    def get_base_static_path(self) -> 'AbstractPath':
        """Gets the base path in this static structure.
        If you know what type if should be, you can cast the results."""
        if isinstance(self, AbstractSubPath):
            parent = self.get_parent_path()
            return parent.get_base_static_path()
        else:
            return self

class AbstractDirPath(AbstractPath, abc.ABC):
    """Extends AbstractPath with the minimum requirements of a path that is a directory."""

    @abc.abstractmethod
    def get_subpaths(self) -> typing.List[AbstractPath]:
        """Gets static directory entires."""
        raise NotImplementedError

    @abc.abstractmethod
    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI) -> bool:
        """Creates just this DirPath.
          Should be forgiving of existing structure.
          Should fail if neccesary.
          Should inform reason via feedback_ui.
          should return True if created or okay.  Should return false upon error.
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

    async def create_routine(self, feedback_ui: AbstractFeedbackUI, recursive=True) -> bool:
        ret = await self.create_self_routine(feedback_ui)
        if recursive:
            for subpath in self.get_subpaths():
                sub_created = await subpath.create_routine(feedback_ui, recursive)
                if sub_created == False:
                    ret = False
        return ret



class AbstractSubPath(AbstractPath, abc.ABC):
    """Extends an AbstractPath with parts neccesary to act as a sub-path of a parent path."""

    _parent_path: AbstractDirPath = None

    def get_parent_path(self) -> AbstractDirPath:
        """The parent path to this sub-path"""
        return self._parent_path

    def __init__(self, parent_path: AbstractDirPath):
        self._parent_path = parent_path


class AutoUpdateResults(Enum):
    #order is important.  We're using a > to deal with reporting recursive status.
    UP_TO_DATE_CLEAN = 1 #all up to date with no dirty assets
    UP_TO_DATE_DIRTY = 2 #all up to date with some dirty assets
    OUT_OF_DATE = 3 #some assets are out of date and can't be brought up to date
    PENDING = 4 #we won't know util we run auto-update again





class AutoCreateResults(Enum):
    NO_CHANGES = 1 #no changes were needed to (re)create this structure.
    CHANGES_MADE = 2 #changes were made to (re)create this structure.
    CANNOT_COMPLETE = 3 #cannot (re)create this structure.



class AbstractGitStorageBasePath(AbstractDirPath, abc.ABC):
    """A base path, which is based on a git storage type.  Either a root or asset."""

    _subpaths: typing.List[AbstractSubPath] = None
    _gitlab_server_name: str = None

    def get_subpaths(self) -> typing.List[AbstractSubPath]:
        return self._subpaths.copy()

    def get_gitlab_server_name(self):
        """The (local) name of the gitlab server this basepath should use for remote operations."""
        return self._gitlab_server_name

    def __init__(self, gitlab_server_name: str):
        self._gitlab_server_name = gitlab_server_name
        self._subpaths = []

    def get_sub_basepaths_recursive(self) -> typing.List["AbstractAssetBasePath"]:
        """A recursive version of get sub basepaths"""
        ret = []
        children = self.get_sub_basepaths()
        ret.extend(children)
        for child in children:
            ret.extend(child.get_sub_basepaths_recursive())
        return ret

    @abc.abstractmethod
    def get_sub_basepaths(self, feedback_ui:AbstractFeedbackUI) -> typing.List["AbstractAssetBasePath"]:
        """Returns a list of AbstratAssetBasePaths that can be reached from inside this GitStorage Base Path.
        Not recursive into further BasePaths.  But yes, recursive through this entire static structure and
        also any dynamically generate-able BasePaths reachable from this static structure.
        e.g. yes, individual named character asset basepaths from within a static 'characters' directory.
        """
        raise NotImplementedError()


    def add_subpath(self, subpath: AbstractSubPath):
        """Add a subpath to this path."""
        subpath._parent_path = self
        self._subpaths.append(subpath)

    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI) -> bool:
        """For a base-path, this just checks for existence.  It'll throw an exception if it doens't already exist."""
        # base paths just check that they exist and move on.
        # a git storage base-path also checks that it can made a valid repo
        path = self.get_path()
        if not os.path.exists(path):
            await feedback_ui.error("Base path doesn't exist: " + path)
            return  False
        if not RepoExists(path):
            await feedback_ui.error("Not a valid git repository: " + path)
            return False
        return True

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

    def is_dirty(self, consider_index:bool, consider_working_tree:bool, consider_untracked_files:bool, consider_submodule_changes:bool):
        """Returns true or false based on whether the worktree is dirty as per the parameters
        :param consider_submodule_changes: whether to consider changes to submodules as making this tree 'dirty'
        :param consider_untracked_files: whether to consider the presence of untrack files as making thsi tree 'dirtt'
        :param consider_working_tree: whether to consider changes to the worktree as making this tree 'dirty'
        :param consider_index: whether to consider changes to the index as making this tree 'dirty'
        """
        repo = Repo(self.get_path())
        return repo.is_dirty(index=consider_index, working_tree=consider_working_tree, untracked_files=consider_untracked_files, submodules=consider_submodule_changes)

    @abc.abstractmethod
    async def auto_update_routine(self, feedback_ui:AbstractFeedbackUI) -> AutoUpdateResults:
        """Auto updates this static structure, providing all feedback to the feedback_ui."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def auto_configure_routine(self, feedback_ui:AbstractFeedbackUI) -> AutoConfigurationResult:
        """Auto (re)configures for this static structure, providing all feedback to the feedback_ui."""
        raise NotImplementedError()

    async def auto_create_routine(self, feedback_ui:AbstractFeedbackUI) -> AutoCreateResults:
        """Auto (re)creates this static structure, providing all feedback to the feedback_ui."""
        exists = await self.check_exists_routine(feedback_ui,True)
        if exists:
            return AutoCreateResults.NO_CHANGES

        created = await self.create_routine(feedback_ui,True)
        if created:
            return AutoCreateResults.CHANGES_MADE
        else:
            return AutoCreateResults.CANNOT_COMPLETE


class AbstractRootBasePath(AbstractGitStorageBasePath):
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
        return GitLabFQDNGitRootRoutines(gitlab_server_routines,root_routines.root,root_routines.root_config)

    async def auto_routine(self, feedback_ui:AbstractFeedbackUI):
        create_results = await self.auto_create_routine(feedback_ui)
        await feedback_ui.output("Running auto (re)creation.")
        if create_results == AutoCreateResults.CANNOT_COMPLETE:
            await feedback_ui.warn("The (re)creation of the structure cannot complete.")
            await feedback_ui.output("Canceling (re)configure and update until it's resolved.")
            return
        await feedback_ui.output("(re)creation result: " + create_results.name)
        await feedback_ui.output("Running auto (re)configuration.")
        configure_results = await self.auto_configure_routine(feedback_ui)
        if configure_results == AutoConfigurationResult.INTERVENTION_REQUIRED:
            await feedback_ui.warn("The (re)configuration of the structure cannot complete and requires user intervention.")
            await feedback_ui.output("Canceling update until it's resolved.")
            return
        await feedback_ui.output("(re)configuration result: " + configure_results.name)
        await feedback_ui.output("Running auto update.")
        update_results = await self.auto_update_routine(feedback_ui)
        await feedback_ui.output("update result: " + update_results.name)


class AbstractAssetBasePath(AbstractGitStorageBasePath):
    """A base-path for a git storage asset."""
    _asset_routines: GitAssetInteractiveRoutines

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

    def __init__(self, gitlab_server_name: str, routines: GitAssetInteractiveRoutines):
        self._asset_routines = routines
        super().__init__(gitlab_server_name)

    def get_path(self) -> str:
        return self._asset_routines.abs_path

    def get_gitlab_asset_routines(self) -> GitLabFQDNGitAssetRoutines:
        """Gets GitLabFQDNGitAssetRooutines for this root."""
        gitlab_server_routines = GitLabServerRoutines(self.get_gitlab_server_name())
        asset_routines = self.get_routines()
        return GitLabFQDNGitAssetRoutines(gitlab_server_routines, asset_routines.working_asset, asset_routines.container.get_fqdn())




class StaticSubDir(AbstractSubPath, AbstractDirPath):
    """A static subdirectory in the static structure.  Implements both SubPath and DirPath.
    Note, it's not a kind of submodule.  It is explicitly a normal subdirectory."""
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

    async def create_self_routine(self, feedback_ui: AbstractFeedbackUI) -> bool:
        path = self.get_path()
        os.makedirs(path, exist_ok=True)
        return True


class AssetsStaticSubDir(StaticSubDir):
    """A static subdirectory that contains N number of git storage assets."""

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

    def get_asset_routines_by_dirname(self, feedback_ui: AbstractFeedbackUI, dirname: str) -> GitAssetInteractiveRoutines:
        """Gets an instance of GitAssetRoutines for a specific named sub-asset.
        Typically, you'll use get_submodules to get a named list, and then use the name to get the Routines.
        It's always possible someone deleted the asset in the interim, resulting in an exception throw."""
        submods = self.get_submodules()
        if dirname not in submods.keys():
            raise FileNotFoundError(dirname)
        submod = submods[dirname]
        base_path = self.get_base_static_path()
        assert isinstance(base_path, AbstractGitStorageBasePath)
        return GitAssetInteractiveRoutines(container_id=base_path.get_container_id(), root_id=base_path.get_root_id(),
                                           asset_id=submod.name, feedback_ui=feedback_ui)

    async def create_new_empty_asset_routine(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        """Creates a new empty asset with a new id at the given directory name.
        Will throw ane exception if the directory exists."""
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

    async def add_from_existing_routine(self, feedback_ui: AbstractFeedbackUI, dirname: str, asset_id: str):
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
        await feedback_ui.output("Adding existing submodule: " + url + " at " + submod_abspath)
        AddSubmodule(repo, asset_id, relpath, url)

    async def subdir_to_new_asset_routine(self, feedback_ui: AbstractFeedbackUI, dirname: str):
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
        await feedback_ui.output("Creating a new submodule from sub-directory at: " + submod_abspath)
        CreateSubmoduleFromSubDirectory(repo, relpath, asset_id, url=url)


TABP = typing.TypeVar("TABP",bound=AbstractAssetBasePath)

class GenericAssetBasePathsSubDir(AssetsStaticSubDir,typing.Generic[TABP]):

    @abc.abstractmethod
    def get_asset_basepath_by_dirname(self, dirname:str, feedback_ui:AbstractFeedbackUI) -> TABP:
        """Create and return an appropriate AssetBasePath for the given dirname"""
        raise NotImplementedError()


    def get_asset_basepaths(self, feedback_ui:AbstractFeedbackUI) -> typing.List[TABP]:
        """Returns a list of AssetBasePaths for submodules that have been checked out."""
        ret = []
        submods = self.get_submodules()
        for dirname in submods.keys():
            submod = submods[dirname]
            #only return a basepath if it's been checked out.
            if submod.module_exists():
                ret.append(self.get_asset_basepath_by_dirname(dirname, feedback_ui))
        return ret

    async def create_and_configure(self, feedback_ui:AbstractFeedbackUI, dirname:str) -> bool:
        base_path = self.get_asset_basepath_by_dirname(dirname,feedback_ui)
        assert isinstance(base_path, AbstractAssetBasePath)
        create_results = base_path.auto_create_routine(feedback_ui)
        if create_results == AutoCreateResults.CANNOT_COMPLETE:
            return False
        configure_results = base_path.auto_configure_routine(feedback_ui)
        if configure_results == AutoConfigurationResult.INTERVENTION_REQUIRED:
            return False
        return True

    async def create_new_empty_asset_routine(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        await super().create_new_empty_asset_routine(feedback_ui, dirname)
        await self.create_and_configure(feedback_ui,dirname)
        return

    async def subdir_to_new_asset_routine(self, feedback_ui: AbstractFeedbackUI, dirname: str):
        await super().subdir_to_new_asset_routine(feedback_ui, dirname)
        await self.create_and_configure(feedback_ui,dirname)
        return


class AbstractDesktopProjectAssetBasePath(AbstractAssetBasePath, abc.ABC):
    """A convenience base path base class for Desktop style project roots.
    Assumes distributed project system, contributed to and pulled by many
    different desktop users across multiple sites/networks/segments/planets/solar-systems/etc."""

    async def auto_update_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoUpdateResults:
        #start with best and downgrade as we go using get_worse.
        ret = AutoUpdateResults.UP_TO_DATE_CLEAN

        #first update all children
        children = self.get_sub_basepaths(feedback_ui)


        for child in children:
            child_status = await child.auto_update_routine(feedback_ui)
            ret = get_worse_enum(ret,child_status)

        #now, collect information about the remote and the local.

        #ahead, behind, detached
        is_ahead = self.remote_is_behind()
        is_behind = self.remote_is_ahead()
        is_detached = self.is_detached()

        asset_routines = self.get_routines()
        gitlab_asset_routines = self.get_gitlab_asset_routines()
        repo = asset_routines.get_repo()

        #dirty. we don't care about submodules.
        is_dirty = repo.is_dirty(index=True,working_tree=True,untracked_files=True,submodules=False)

        #checking for conflicts
        unmerged_blobs = repo.index.unmerged_blobs()
        conflicted = False
        for path in unmerged_blobs:
            list_of_blobs = unmerged_blobs[path]
            for (stage, blob) in list_of_blobs:
                # Now we can check each stage to see whether there were any conflicts
                if stage != 0:
                    conflicted = True

        #if we're conflicted, inform, and we're done.  can't auto fix conflicts.
        if conflicted:
            await feedback_ui.warn(self.get_path() + " is conflicted.")
            await feedback_ui.output("You will need to resolve conflicts or cancel the merge.")
            return get_worse_enum(ret,AutoUpdateResults.OUT_OF_DATE)


        #if we're dirty (ignoring submodules) inform, advise and we're done.
        #bonus, we also warn if we're behind and suggest manual intervetion to merge.
        if is_dirty:
            await feedback_ui.warn("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + " is dirty.")
            await feedback_ui.output("Once you are done making changes, you'll want to either commit them, or revert them.")
            if is_behind:
                await feedback_ui.warn("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + " also has upstream changes.")
                await feedback_ui.output("You may wish to merge in the changes, or you could wait and do it later.")
                return get_worse_enum(ret,AutoUpdateResults.OUT_OF_DATE)
            else:
                return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_DIRTY)


        #if we're detached, we checkout.
        if is_detached:
            await feedback_ui.output("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + "has a detached head, but is clean.")
            await feedback_ui.output("Checking out the 'master' branch at HEAD.")
            output = repo.git.checkout("master")
            await feedback_ui.output(output)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #ahead and not behind, is a push.
        if is_ahead and not is_behind:
            await feedback_ui.output("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + "is ahead and clean, and will be pushed.")
            await gitlab_asset_routines.push_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_CLEAN)

        #any pull could leave us conflicted.  If we are left conflicted, that's handled the next time we auto-update.

        #behind, is a pull.
        if not is_ahead and is_behind:
            await feedback_ui.output("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + "is behind but clean, and will be pulled.")
            await gitlab_asset_routines.pull_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #ahead and behind is a pull.
        if is_ahead and is_behind:
            await feedback_ui.output("Desktop asset " + asset_routines.container.GetShortName() + "/" +asset_routines.root.GetName() + "/" + asset_routines.relative_path + "is behind and ahead, but clean, and will be pulled.")
            await gitlab_asset_routines.pull_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #if we got here, most likely, we're up to date and clean.
        return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_CLEAN)


class AbstractDesktopProjectRootBasePath(AbstractRootBasePath, abc.ABC):
    """A convenience base path base class for Desktop style project roots.
    Assumes distributed project system, contributed to and pulled by many
    different desktop users across multiple sites/networks/segments/planets/solar-systems/etc."""

    async def auto_update_routine(self, feedback_ui:AbstractFeedbackUI):
        """Desktop Root auto update behavior."""

        #start with best and downgrade as we go using get_worse.
        ret = AutoUpdateResults.UP_TO_DATE_CLEAN

        #first update all children
        children = self.get_sub_basepaths(feedback_ui)


        for child in children:
            child_status = await child.auto_update_routine(feedback_ui)
            ret = get_worse_enum(ret,child_status)

        #now, collect information about the remote and the local.

        #ahead, behind, detached
        is_ahead = self.remote_is_behind()
        is_behind = self.remote_is_ahead()
        is_detached = self.is_detached()


        root_routines = self.get_routines()
        gitlab_root_routines = self.get_gitlab_root_routines()
        repo = root_routines.get_local_repo()

        #dirty. we don't care about submodules.
        is_dirty = repo.is_dirty(index=True,working_tree=True,untracked_files=True,submodules=False)

        #checking for conflicts
        unmerged_blobs = repo.index.unmerged_blobs()
        conflicted = False
        for path in unmerged_blobs:
            list_of_blobs = unmerged_blobs[path]
            for (stage, blob) in list_of_blobs:
                # Now we can check each stage to see whether there were any conflicts
                if stage != 0:
                    conflicted = True

        #if we're conflicted, inform, and we're done.  can't auto fix conflicts.
        if conflicted:
            await feedback_ui.warn(self.get_path() + " is conflicted.")
            await feedback_ui.output("You will need to resolve conflicts or cancel the merge.")
            return get_worse_enum(ret,AutoUpdateResults.OUT_OF_DATE)


        #if we're dirty (ignoring submodules) inform, advise and we're done.
        #bonus, we also warn if we're behind and suggest manual intervetion to merge.
        if is_dirty:
            await feedback_ui.warn("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + " is dirty.")
            await feedback_ui.output("Once you are done making changes, you'll want to either commit them, or revert them.")
            if is_behind:
                await feedback_ui.warn("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + " also has upstream changes.")
                await feedback_ui.output("You may wish to merge in the changes, or you could wait and do it later.")
                return get_worse_enum(ret,AutoUpdateResults.OUT_OF_DATE)
            else:
                return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_DIRTY)


        #if we're detached, we checkout.
        if is_detached:
            await feedback_ui.output("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + "has a detached head, but is clean.")
            await feedback_ui.output("Checking out the 'master' branch at HEAD.")
            output = repo.git.checkout("master")
            await feedback_ui.output(output)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #ahead and not behind, is a push.
        if is_ahead and not is_behind:
            await feedback_ui.output("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + "is ahead and clean, and will be pushed.")
            await gitlab_root_routines.push_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_CLEAN)

        #any pull could leave us conflicted.  If we are left conflicted, that's handled the next time we auto-update.

        #behind, is a pull.
        if not is_ahead and is_behind:
            await feedback_ui.output("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + "is behind but clean, and will be pulled.")
            await gitlab_root_routines.pull_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #ahead and behind is a pull.
        if is_ahead and is_behind:
            await feedback_ui.output("Desktop root " + root_routines.container.GetShortName() + "/" + root_routines.root.GetName() + "is behind and ahead, but clean, and will be pulled.")
            await gitlab_root_routines.pull_routine(feedback_ui)
            return get_worse_enum(ret,AutoUpdateResults.PENDING) #we won't know if we're up to date until the next run.

        #if we got here, most likely, we're up to date and clean.
        return get_worse_enum(ret,AutoUpdateResults.UP_TO_DATE_CLEAN)
