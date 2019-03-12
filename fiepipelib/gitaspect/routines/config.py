import abc
import typing
from abc import ABCMeta

import git

from fiepipelib.gitaspect.data.config import GitAspectConfiguration

T = typing.TypeVar("T", bound=GitAspectConfiguration)


class GitAspectConfigurationRoutines(typing.Generic[T], metaclass=ABCMeta):

    _config: T = None

    def __init__(self, config: T):
        self._config = config


    def get_configuration(self) -> T:
        return self._config

    def get_asset_path(self) -> str:
        return self.get_configuration().get_worktree_path()

    def get_asset_repo(self) -> git.Repo:
        return git.Repo(self.get_asset_path())

    def load(self):
        self.get_configuration().load()

    def commit(self):
        self.get_configuration().commit()
        repo = git.Repo(self.get_configuration().get_worktree_path())
        repo.git.add(self.get_configuration().get_config_path())

    def is_configured(self) -> bool:
        config = self.get_configuration()
        return config.exists()

    @abc.abstractmethod
    def default_configuration(self):
        """Populate the given configuration with defaults."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def reconfigure_interactive_routine(self):
        """Reconfigure the aspect in an interactive manner."""
        raise NotImplementedError()

    async def create_update_configuration_interactive_routine(self):

        # create/update/write
        configuration = self.get_configuration()
        if not configuration.exists():
            self.default_configuration()
        else:
            configuration.load()
        await self.reconfigure_interactive_routine()
        configuration.commit()

        # add to git
        repo = git.Repo(configuration.get_worktree_path())
        repo.git.add(configuration.get_config_path())