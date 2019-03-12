import abc
import typing

from fiepipelib.assetaspect.data.config import AssetAspectConfiguration
from fiepipelib.assetaspect.routines.config import AssetAspectConfigurationRoutines
from fiepipelib.gitaspect.shell.config import GitConfigCommand
from fiepipelib.gitstorage.shells.gitasset import Shell as GitAssetShell

TA = typing.TypeVar("TA", bound=AssetAspectConfiguration)


class AssetConfigCommand(GitConfigCommand[TA], typing.Generic[TA]):
    _asset_shell: GitAssetShell = None

    def get_asset_shell(self) -> GitAssetShell:
        return self._asset_shell

    def __init__(self, asset_shell: GitAssetShell):
        self._asset_shell = asset_shell
        super(AssetConfigCommand, self).__init__()

    @abc.abstractmethod
    def get_configuration_routines(self) -> AssetAspectConfigurationRoutines[TA]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AssetConfigCommand, self).get_plugin_names_v1()
        ret.append("assetaspect_configuration_command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self._asset_shell.get_prompt_text(),
                                           self.get_configuration_data().get_config_name()])

    def do_update_git_meta(self, args):
        """Updates git meta-data for this aspect.  Meaning it updates .gitignore and lfs tracking
        based on the configuration.

        Usually this is done automatically every time the config is commited (changed).  However,
        this will force and update regardless.  Code/plugin changes might be a good example situation where
        this command is needed.

        Usage: udpate_git_meta"""
        routines = self.get_configuration_routines()
        routines.load()
        routines.update_git_meta()
