import abc
import typing
import git

from fiepipelib.assetaspect.data.config import AspectConfiguration
from fieui.FeedbackUI import AbstractFeedbackUI

T = typing.TypeVar("T", bound=AspectConfiguration)


class AspectConfigurationRoutines(typing.Generic[T]):

    _config: T = None

    def get_configuration(self) -> T:
        return self._config

    def __init__(self, config:T):
        self._config = config

    def load(self):
        self.get_configuration().load()

    def commit(self):
        self.get_configuration().commit()
        repo = git.Repo(self.get_configuration().asset_path)
        repo.git.add(self.get_configuration().get_config_path())


    @abc.abstractmethod
    def default_configuration(self):
        """Populate the given configuration with defaults."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def reconfigure(self):
        raise NotImplementedError()

    async def create_update_configuration(self):
        configuration = self.get_configuration()
        if not configuration.exists():
            self.default_configuration()
        else:
            configuration.load()
        await self.reconfigure()
        configuration.commit()
        repo = git.Repo(configuration.asset_path)
        repo.git.add(configuration.get_config_path())

