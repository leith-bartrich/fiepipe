import abc
import typing

from fiepipelib.gitaspect.data.config import GitAspectConfiguration
from fiepipelib.gitaspect.routines.config import GitAspectConfigurationRoutines
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T", bound=GitAspectConfiguration)


class GitConfigCommand(AbstractShell, typing.Generic[T]):

    @abc.abstractmethod
    def get_configuration_data(self) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_configuration_routines(self) -> GitAspectConfigurationRoutines[T]:
        raise NotImplementedError()

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