import abc
import typing

from fiepipelib.gitaspect.data.config import GitAspectConfiguration


class AssetAspectConfiguration(GitAspectConfiguration, abc.ABC):

    @abc.abstractmethod
    def get_lfs_patterns(self) -> typing.List[str]:
        """Returns a list of asset-wide lfs patterns to track.
        e.g. ['*.jpg','foo/**/bar.txt']"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_git_ignores(self) -> typing.List[str]:
        """Returns a list of asset-wide ignores for git.
        e.g. ['localstuff.ini','*.dll']"""
        raise NotImplementedError()

    _asset_path: str = None

    def get_worktree_path(self) -> str:
        return self._asset_path

    def __init__(self, asset_path: str):
        self._asset_path = asset_path

    @property
    def asset_path(self):
        return self._asset_path
