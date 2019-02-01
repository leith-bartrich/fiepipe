import abc
import typing

from fiepipelib.assetaspect.data.config import AspectConfiguration
from fiepipelib.assetaspect.routines.config import AspectConfigurationRoutines
from fiepipelib.gitstorage.shells.gitasset import Shell as GitAssetShell, AvailableAspect
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T", bound=AspectConfiguration)


class ConfigCommand(AbstractShell, typing.Generic[T]):
    _asset_shell: GitAssetShell = None

    def get_asset_shell(self) -> GitAssetShell:
        return self._asset_shell

    def __init__(self, asset_shell: GitAssetShell):
        self._asset_shell = asset_shell
        super(ConfigCommand, self).__init__()

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(ConfigCommand, self).get_plugin_names_v1()
        ret.append("assetaspect_configuration_command")
        return ret

    @abc.abstractmethod
    def get_configuration_data(self) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_configuration_routines(self) -> AspectConfigurationRoutines[T]:
        raise NotImplementedError()

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self._asset_shell.get_prompt_text(),
                                           self.get_configuration_data().get_config_name()])

    def do_is_configured(self, args):
        """Prints indication as to if the asset has this configuration or not.

        Usage: is_configured"""

        args = self.parse_arguments(args)

        config_data = self.get_configuration_data()
        if config_data.exists():
            self.poutput("Yes")
        else:
            self.poutput("No")

    def do_configure(self, args):
        """(Re)Configures this aspect.

        Usage: configure"""
        routines = self.get_configuration_routines()
        self.do_coroutine(routines.create_update_configuration_interactive_routine())

    def do_unconfigure(self, args):
        """Unconfigures (removes the configuration for) this aspect.

        Usage: deconfigure"""
        config_data = self.get_configuration_data()
        if config_data.exists():
            config_data.delete()

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


