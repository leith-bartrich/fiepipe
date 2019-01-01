import abc
import typing
import git

from fiepipelib.assetaspect.data.config import AspectConfiguration
from fieui.FeedbackUI import AbstractFeedbackUI
from fiepipelib.git.routines.ignore import AddIgnore, CheckCreateIgnore
from fiepipelib.git.routines.lfs import InstallLFSRepo, Track
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.data.local_root_configuration import LocalRootConfiguration
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines


T = typing.TypeVar("T", bound=AspectConfiguration)


class AspectConfigurationRoutines(typing.Generic[T]):

    _config: T = None
    _asset_routines:GitAssetRoutines = None

    def get_configuration(self) -> T:
        return self._config

    def get_asset_path(self) -> str:
        return self.get_configuration().asset_path

    def get_asset_repo(self) -> git.Repo:
        return git.Repo(self.get_asset_path())

    def get_working_asset(self) -> GitWorkingAsset:
        return GitWorkingAsset(self.get_asset_repo())

    def get_asset_routines(self) -> GitAssetRoutines:
        return self._asset_routines

    def __init__(self, config:T,asset_routines:GitAssetRoutines):
        self._config = config
        self._asset_routines = asset_routines

    def load(self):
        self.get_configuration().load()

    def commit(self):
        self.get_configuration().commit()
        repo = git.Repo(self.get_configuration().asset_path)
        repo.git.add(self.get_configuration().get_config_path())
        self.update_git_meta()


    @abc.abstractmethod
    def default_configuration(self):
        """Populate the given configuration with defaults."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def reconfigure(self):
        raise NotImplementedError()

    async def create_update_configuration(self):

        #create/update/write
        configuration = self.get_configuration()
        if not configuration.exists():
            self.default_configuration()
        else:
            configuration.load()
        await self.reconfigure()
        configuration.commit()

        #add to git
        repo = git.Repo(configuration.asset_path)
        repo.git.add(configuration.get_config_path())
        self.update_git_meta()



    def update_git_meta(self):
        configuration = self.get_configuration()
        repo = git.Repo(configuration.asset_path)

        #update ignore and lfs track
        lfs_patterns = configuration.get_lfs_patterns()
        git_ignores = configuration.get_git_ignores()
        CheckCreateIgnore(repo)
        for ignore in git_ignores:
            AddIgnore(repo,ignore)
        CheckCreateIgnore(repo)
        InstallLFSRepo(repo)
        Track(repo,lfs_patterns)
