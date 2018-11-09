import abc
import typing

from fiepipelib.locallymanagedtypes.data.abstractmanager import AbstractUserLocalTypeManager


class AbstractSimpleApplicationInstall(object):
    _name: str = None
    _path: str = None

    def get_name(self) -> str:
        return self._name

    def get_path(self) -> str:
        return self._path


T = typing.TypeVar("T", bound=AbstractSimpleApplicationInstall)


class AbstractSimpleApplicationInstallsManager(AbstractUserLocalTypeManager[T], abc.ABC):

    @abc.abstractmethod
    def get_application_name(self) -> str:
        raise NotImplementedError()

    def GetManagedTypeName(self) -> str:
        return self.get_application_name() + "_installs"

    def GetColumns(self) -> typing.List[typing.Tuple[str, str]]:
        ret = super().GetColumns()
        ret.append(('name', 'text'))
        return ret

    def GetPrimaryKeyColumns(self) -> typing.List[str]:
        return ['name']

    def ToJSONData(self, item: T) -> dict:
        ret = {}
        ret['name'] = item.get_name()
        ret['path'] = item.get_path()
        return ret

    @abc.abstractmethod
    def new_empty(self) -> T:
        raise NotImplementedError()

    def FromJSONData(self, data: dict) -> T:
        ret = self.new_empty()
        ret._name = data['name']
        ret._path = data['path']
        return ret

    def FromParameters(self, name: str, path: str) -> T:
        ret = self.new_empty()
        ret._name = name
        ret._path = path
        return ret

    def get_by_name(self, name: str) -> T:
        return self._Get([('name', name)])[0]

    def delete_by_name(self, name: str):
        self._Delete('name', name)