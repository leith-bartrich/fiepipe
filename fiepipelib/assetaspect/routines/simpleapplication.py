import abc
import typing

from fiepipelib.assetaspect.data.simpleapplication import AbstractSimpleApplicationInstall, \
    AbstractSimpleApplicationInstallsManager
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedRoutines
from fiepipelib.ui.abspath_input_ui import AbstractAbspathDefaultInputUI
from fieui.FeedbackUI import AbstractFeedbackUI

T = typing.TypeVar("T", bound=AbstractSimpleApplicationInstall)


class AbstractSimpleApplicationRoutines(AbstractLocalManagedRoutines[T]):
    _path_input_ui: AbstractAbspathDefaultInputUI = None

    def __init__(self, feedback_ui: AbstractFeedbackUI, path_input_ui: AbstractAbspathDefaultInputUI):
        self._path_input_ui = path_input_ui
        super().__init__(feedback_ui)

    @abc.abstractmethod
    def GetManager(self) -> AbstractSimpleApplicationInstallsManager[T]:
        raise NotImplementedError()

    def GetAllItems(self) -> typing.List[T]:
        man = self.GetManager()
        return man.GetAll()

    def ItemToName(self, item: T) -> str:
        return item.get_name()

    def GetItemByName(self, name: str) -> T:
        man = self.GetManager()
        return man.get_by_name(name)

    async def DeleteRoutine(self, name: str):
        man = self.GetManager()
        man.delete_by_name(name)

    async def CreateUpdateRoutine(self, name: str):
        man = self.GetManager()
        try:
            item = man.get_by_name(name)
        except LookupError:
            item = man.FromParameters(name, ".")
        path = await self._path_input_ui.execute("Path to " + man.get_application_name(), item.get_path())
        item._path = path
        man.Set([item])