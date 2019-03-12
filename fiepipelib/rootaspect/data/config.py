import abc
import os

from fiepipelib.gitaspect.data.config import GitAspectConfiguration


class RootAsepctConfiguration(GitAspectConfiguration, abc.ABC):
    _worktree_path: str = None

    def get_worktree_path(self) -> str:
        return self._worktree_path

    def __init__(self, worktree_path: str):
        self._worktree_path = worktree_path

    def get_config_dir_path(self) -> str:
        return os.path.join(self.get_worktree_path(), 'root_configs')

