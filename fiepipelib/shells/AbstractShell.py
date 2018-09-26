import abc
import typing
import fieuishell.Shell
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines

class AbstractShell(fieuishell.Shell.Shell):
    """An abstract base class for fiepipe shells."""

    def get_plugin_prepend(self):
        return "fiepipe.plugin.shell."

    def get_plugin_postpend(self):
        return ".v1"

    @abc.abstractmethod
    def get_plugin_names_v1(self) -> typing.List[str]:
        """All subclasses should override this, and call super.  Append to the list and return."""
        ret = super().get_plugin_names_v1()
        return ret

    def do_clear(self, arg):
        """Clears the console screen."""
        platform = get_local_platform_routines()
        cmd = platform.get_console_clear_command()
        self.do_shell(cmd)


