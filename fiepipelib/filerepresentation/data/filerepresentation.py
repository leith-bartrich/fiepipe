import abc
import os.path
import pathlib
import typing

import fiepipelib.assetdata
from fiepipelib.assetdata.data.items import AbstractItemManager
from fiepipelib.fileversion.data.fileversion import AbstractFileVersion
from fiepipelib.assetdata.data.connection import Connection, GetConnection

class AbstractRepresentation(object):

    _name = None
    _path = None
    _version =  None

    def GetAbsolutePath(self, version:AbstractFileVersion):
        return os.path.join(os.path.dirname(version.GetAbsolutePath()),version.GetFullName() + ".representations",self._path)

    def DeleteFiles(self, version:AbstractFileVersion):
        p = pathlib.Path(self.GetAbsolutePath(version))
        if p.exists():
            if p.is_dir:
                shutil.rmtree(str(p), ignore_errors=False)
            else:
                p.unlink()

    def GetPath(self):
        return self._path

    def GetName(self):
        return self._name

    def GetVersion(self) -> str:
        return self._version


class AbstractRepresentationManager(AbstractItemManager):

    @abc.abstractmethod
    def GetRepresentationColumns(self) -> typing.List[typing.Tuple[str,str]]:
        raise NotImplementedError()

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(('name','text'))
        ret.append(('path','text'))
        ret.append(('version','text'))
        for col in self.GetRepresentationColumns():
            ret.append(col)
        return ret

    @abc.abstractmethod
    def GetRepresentationPrimaryKeyColumns(self) -> typing.List[str]:
        raise NotImplementedError()

    def GetPrimaryKeyColumns(self):
        ret = ['version','name']
        for col in self.GetRepresentationPrimaryKeyColumns():
            ret.append(col)
        return ret

    @abc.abstractclassmethod
    def GetByVersion(self, version:AbstractFileVersion, connection: Connection):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def GetByName(self, name:str, version:AbstractFileVersion, connection: Connection):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def DeleteByName(self, name:str, version:AbstractFileVersion, connection: Connection):
        raise NotImplementedError()


def AbstractRepresentationFromJSON(data:dict, rep: AbstractRepresentation):
    ret = rep
    ret._name = data['name']
    ret._path = data['path']
    ret._version = data['version']


def AbstractRepresentationToJSON(rep: AbstractRepresentation, data:dict):
    ret = data
    ret['name'] = rep._name
    ret['path'] = rep._path
    ret['version'] = rep._version


def AbstractRepresentationFromParameters(name:str, path:str, version:str, rep: AbstractRepresentation):
    ret = rep
    ret._name = name
    ret._path = path
    ret._version = version