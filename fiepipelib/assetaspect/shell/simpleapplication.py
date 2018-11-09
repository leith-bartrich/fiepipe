import abc
import typing

from fiepipelib.assetaspect.data.simpleapplication import AbstractSimpleApplicationInstall
from fiepipelib.assetaspect.routines.simpleapplication import AbstractSimpleApplicationRoutines
from fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand import LocalManagedTypeCommand
from fiepipelib.shells.AbstractShell import AbstractShell

T = typing.TypeVar("T", bound=AbstractSimpleApplicationInstall)


class AbstractSimpleApplicationCommand(LocalManagedTypeCommand[T]):

    @abc.abstractmethod
    def get_routines(self) -> AbstractSimpleApplicationRoutines[T]:
        raise NotImplementedError()

    def get_shell(self, item) -> AbstractShell:
        return super(AbstractSimpleApplicationCommand, self).get_shell(item)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(AbstractSimpleApplicationCommand, self).get_plugin_names_v1()
        app_name = self.get_routines().GetManager().get_application_name()
        ret.append(app_name + "_installs_command")
        return ret

    def get_prompt_text(self) -> str:
        app_name = self.get_routines().GetManager().get_application_name()
        return self.prompt_separator.join(['fiepipe', app_name + '_installs'])