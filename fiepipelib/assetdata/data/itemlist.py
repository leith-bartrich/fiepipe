import abc
import typing

import fiepipelib.assetdata
from fiepipelib.assetdata.data.items import AbstractItemManager
from fiepipelib.assetdata.data.link import AbstractLink, AbstractLinkTableManager


class AbstractItemList(object):

    _name = None
    _desc = None

    def GetName(self) -> str:
        return self._name

    def GetDescription(self) -> str:
        return self._desc


class AbstractItemListManager(AbstractItemManager):

    def FromJSONData(self, data) -> AbstractItemList:
        """Override and call super() to add more data."""
        ret = self.NewList()
        ret._name = data['name']
        ret._desc = data['desc']
        return ret

    def ToJSONData(self, item:AbstractItemList) -> typing.Dict:
        ret = {}
        ret['name'] = item._name
        ret['desc'] = item._desc
        return ret

    @abc.abstractmethod
    def NewList(self) -> AbstractItemList:
        raise NotImplementedError()

    def NewListFromParameters(self, name:str, desc:str) -> AbstractItemList:
        """Override, add args and call super() to add more data."""
        ret = self.NewList()
        ret._name = name
        ret._desc = desc
        return ret

    def GetColumns(self):
        """Override and call super() to add data columns"""
        ret = super().GetColumns()
        ret.append(("name","text"))
        return ret

    def GetPrimaryKeyColumns(self):
        ret = []
        ret.append("name")
        return ret

    def GetByName(self, name, conn: fiepipelib.assetdata.data.connection.Connection):
        return self._Get(conn.GetDBConnection(), ['name',name])

    def DeleteByName(self, name, conn: fiepipelib.assetdata.data.connection.Connection):
        self._Delete("name", name, conn.GetDBConnection())


class AbstractItemListEntry(AbstractLink):

    def GetList(self, conn: fiepipelib.assetdata.data.connection.Connection) -> AbstractItemList:
        return self.GetFirst( conn)

    def GetItem(self, conn: fiepipelib.assetdata.data.connection.Connection):
        return self.GetSecond( conn)


class AbstractItemListEntryManager(AbstractLinkTableManager):

    def ClearList(self, lst:AbstractItemList, conn: fiepipelib.assetdata.data.connection.Connection):
        self.DeleteByFirst(list, conn)

    def RemoveFromLists(self, item, conn: fiepipelib.assetdata.data.connection.Connection):
        self.DeleteBySecond(item, conn)