import abc
import pathlib
import typing

import fiepipelib.assetdata
import fiepipelib.gitstorage
from fiepipelib.assetdata.data.items import AbstractItemManager


class AbstractFileVersionManager(AbstractItemManager):

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(('version','text'))
        return ret

    def GetCompoundKeyColumns(self) -> typing.List[str]:
        """Override this.
        Return a list of column names (str)
        of columns other than 'version' that make up the compound key."""
        raise NotImplementedError()

    def GetPrimaryKeyColumns(self):
        ck = self.GetCompoundKeyColumns()
        #might want to search for existing 'versions' just incase?
        ck.append("version")
        return ck


class AbstractFileVersion(object):

    _version = None
    _workingAsset = None

    def GetVersion(self) -> str:
        return self._version

    def GetWorkingAsset(self) -> fiepipelib.gitstorage.data.git_working_asset.GitWorkingAsset:
        return self._workingAsset

    @abc.abstractmethod
    def GetFullName(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def GetFilename(self):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def GetAbsolutePath(self):
        raise NotImplementedError()

    def FileExists(self):
        p = pathlib.Path(self.GetAbsolutePath())
        return p.exists() & p.is_file()

    def EnsureDirExists(self):
        pdir = pathlib.Path(self.GetDirPath())
        if not pdir.exists():
            pdir.mkdir(parents=True, exist_ok=True)

    def GetDirPath(self):
        p = pathlib.Path(self.GetAbsolutePath())
        pdir = pathlib.Path(p.parent)
        return str(pdir)


def LatestVersion(versions:typing.List[AbstractFileVersion],fqdn:str):
    if len(versions) == 0:
        return None

    verman = fiepipelib.versions.comparison.GetVersionComparisonManager()

    latest = versions[0]
    for i in range(0,len(versions)):
        if verman.Compare(latest,versions[i],fqdn) == -1:
            latest = versions[i]
    return latest


def AbstractFileVersionToJSON(afv:AbstractFileVersion, data:typing.Dict):
    data['version'] = afv._version
    return data


def AbstractFileVersionFromJSON(afv:AbstractFileVersion, data:typing.Dict, workingAsset: fiepipelib.gitstorage.data.git_working_asset.GitWorkingAsset):
    afv._version = data['version']
    afv._workingAsset = workingAsset
    return afv


def AbstractFileVersionFromParameters(afv: AbstractFileVersion, version:str, workingAsset: fiepipelib.gitstorage.data.git_working_asset.GitWorkingAsset):
    afv._version = version
    afv._workingAsset = workingAsset
    return afv


