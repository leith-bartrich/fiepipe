import abc
import typing

from fiepipelib.gitaspect.shell.config import GitConfigCommand
from fiepipelib.gitstorage.shells.gitroot import Shell as GitRootShell
from fiepipelib.rootaspect.data.config import RootAsepctConfiguration
from fiepipelib.rootaspect.routines.config import RootAspectConfigurationRoutines

TR = typing.TypeVar("TR", bound=RootAsepctConfiguration)


class RootConfigCommand(GitConfigCommand[TR], typing.Generic[TR]):
    _root_shell: GitRootShell = None

    def get_root_shell(self) -> GitRootShell:
        return self._root_shell

    def __init__(self, root_shell: GitRootShell):
        self._root_shell = root_shell
        super(RootConfigCommand, self).__init__()

    @abc.abstractmethod
    def get_configuration_routines(self) -> RootAspectConfigurationRoutines[TR]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(GitConfigCommand, self).get_plugin_names_v1()
        ret.append("rootaspect_configuration_command")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join([self._root_shell.get_prompt_text(),
                                           self.get_configuration_data().get_config_name()])