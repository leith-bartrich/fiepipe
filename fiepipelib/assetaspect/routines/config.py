import abc
import typing

import git

from fiepipelib.assetaspect.data.config import AssetAspectConfiguration
from fiepipelib.assetaspect.routines.autoconf import AutoConfigurationResult
from fiepipelib.enum import get_worse_enum
from fiepipelib.git.routines.ignore import AddIgnore, CheckCreateIgnore
from fiepipelib.git.routines.lfs import InstallLFSRepo, Track, LFSIsInstalledRepo
from fiepipelib.gitaspect.routines.config import GitAspectConfigurationRoutines
from fiepipelib.gitstorage.data.git_working_asset import GitWorkingAsset
from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
from fieui.FeedbackUI import AbstractFeedbackUI

TA = typing.TypeVar("TA", bound=AssetAspectConfiguration)


class AssetAspectConfigurationRoutines(GitAspectConfigurationRoutines[TA], typing.Generic[TA]):
    _asset_routines: GitAssetRoutines = None

    def get_working_asset(self) -> GitWorkingAsset:
        return GitWorkingAsset(self.get_asset_repo())

    def get_asset_routines(self) -> GitAssetRoutines:
        return self._asset_routines

    def __init__(self, config: TA, asset_routines: GitAssetRoutines):
        self._asset_routines = asset_routines
        super(AssetAspectConfigurationRoutines, self).__init__(config)

    def commit(self):
        super(AssetAspectConfigurationRoutines, self).commit()
        self.update_git_meta()

    @abc.abstractmethod
    async def auto_reconfigure_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoConfigurationResult:
        """Reconfigure the aspect automatically if possible.
        Return the result based on what happened."""
        raise NotImplementedError()

    async def auto_configure_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoConfigurationResult:
        """
        Called by the structure or project managment systems to configure, or reconfigure this
        aspect in a programmatic manner.  With no user intervention.  Feedback should be provided via
        the passed feedback_ui.

        The Result can be INTERVENTION_REQUIRED if neccesary.

        The responsibilities at a simple level are:
          -configure if not configured.
          -update any update-able configuration.

        One should expect auto-configure to be run often.

        auto update git-meta data if neccesary.  Tries not to if not neccesary.
        """

        ret = AutoConfigurationResult.NO_CHANGES

        # create/update/write
        configuration = self.get_configuration()
        if not configuration.exists():
            self.default_configuration()
            ret = get_worse_enum(ret, AutoConfigurationResult.CHANGES_MADE)
        else:
            configuration.load()
        reconfigure_result = await self.auto_reconfigure_routine(feedback_ui)
        ret = get_worse_enum(ret, reconfigure_result)

        if ret != AutoConfigurationResult.NO_CHANGES:
            if ret != AutoConfigurationResult.INTERVENTION_REQUIRED:
                configuration.commit()
                repo = git.Repo(configuration.get_worktree_path())
                repo.git.add(configuration.get_config_path())
                self.update_git_meta()

        return ret

    async def create_update_configuration_interactive_routine(self):
        await super(AssetAspectConfigurationRoutines, self).create_update_configuration_interactive_routine()
        self.update_git_meta()

    def update_git_meta(self):
        """Makes changes to the git meta-data system based
        on the configuration.  Such as ignores and lfs tracked files.

        note: currently slow because we can't/don't always check for
        existing entries as efficiently as we should"""
        configuration = self.get_configuration()
        repo = git.Repo(configuration.get_worktree_path())

        # update ignore and lfs track
        lfs_patterns = configuration.get_lfs_patterns()
        git_ignores = configuration.get_git_ignores()

        CheckCreateIgnore(repo)
        for ignore in git_ignores:
            AddIgnore(repo, ignore)
        CheckCreateIgnore(repo)
        if not LFSIsInstalledRepo(repo):
            InstallLFSRepo(repo)
        Track(repo, lfs_patterns)
