import abc
import typing
from abc import ABCMeta, abstractmethod

import git
import pkg_resources

from fiepipelib.git.routines.lfs import Track


class GitRepoRoutines(object, metaclass=ABCMeta):

    @abc.abstractmethod
    def get_repo(self) -> git.Repo:
        raise NotImplementedError()

    @abc.abstractmethod
    def load(self):
        raise NotImplementedError()


    @abc.abstractmethod
    def can_commit(self) -> (bool, str):
        """Returns a tuple of bool,str. False if its easily determined that the given GitRepo cannot currently commit cleanly.
        This is not a guarontee of a succesful commit.  The string should give a 'reason' to report to the user if
        possible."""
        raise NotImplementedError()

    # async def update_lfs_track_patterns(self):
    #     """Updates the tracked patterns for lfs for this repo.
    #
    #     Calls all plugins of type: fiepipe.plugin.gitstorage.lfs.patterns
    #     Where the method signature is (gitRepoRoutines:GitRepoRoutines, patterns:List[str])
    #     The patterns list should be added/appended/modified to contain a list of
    #     lfs patterns to track.  The list will have been modified by other plugins prior.  Care
    #     should be taken not to trample other plugins additions.
    #
    #     The GitRepoRoutines argument provides all kinds of context by which to make decisions.  It will have been 'loaded'
    #     prior to being passed.  And one can check if it implements a pariticular subclass such as GitAssetRoutines or
    #     GitRootRoutines
    #     """
    #     repo = self.get_repo()
    #     patterns = []
    #
    #     entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.gitstorage.lfs.patterns")
    #     for entrypoint in entrypoints:
    #         method = entrypoint.load()
    #         method(self, patterns)
    #     Track(repo, patterns)

    def get_untracked(self) -> typing.List[str]:
        repo = self.get_repo()
        return repo.untracked_files.copy()

    def has_untracked(self) -> bool:
        return len(self.get_untracked()) > 0

    def get_modified(self) -> typing.List[str]:
        # ret = []
        repo = self.get_repo()
        changed = [item.a_path for item in repo.index.diff(None)]
        # untracked_files = self.get_untracked()
        # for path in changed:
        #     if path not in untracked_files:
        #         ret.append(path)
        return changed

    def _add_submodules_recursive(self, repo: git.Repo):
        for submod in repo.submodules:
            assert isinstance(submod, git.Submodule)
            if submod.module_exists():
                self._add_submodules_recursive(submod.module())
                repo.git.add(submod.path)

    def add_submodule_versions(self):
        repo = self.get_repo()
        self._add_submodules_recursive(repo)

    @abstractmethod
    def check_create_change_dir(self):
        pass