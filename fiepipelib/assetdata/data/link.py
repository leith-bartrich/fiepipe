import abc
import typing

import fiepipelib.assetdata
from fiepipelib.assetdata.data.items import AbstractItemManager


class AbstractLink(object):
    _linkManager = None
    _firstColsAndValues = None
    _secondColsAndValues = None

    def __init__(self, manager: 'AbstractLinkTableManager'):
        self._linkManager = manager

    def GetFirst(self, conn: fiepipelib.assetdata.data.connection.Connection) -> typing.List:
        return self._linkManager._firstManager._Get(conn.GetDBConnection(), self._firstColsAndValues)

    def GetSecond(self, conn: fiepipelib.assetdata.data.connection.Connection) -> typing.List:
        return self._linkManager._secondManager._Get(conn.GetDBConnection(), self._secondColsAndValues)

    def _setFirst(self, item):
        data = self._linkManager._firstManager.ToJSONData(item)
        keyCols = self._linkManager._firstManager.GetPrimaryKeyColumns()
        colsAndVal = []
        for key in keyCols:
            colsAndVal[key] = data[key]
        self._firstColsAndValues = colsAndVal

    def _setSecond(self, item):
        data = self._linkManager._secondManager.ToJSONData(item)
        keyCols = self._linkManager._secondManager.GetPrimaryKeyColumns()
        colsAndVal = []
        for key in keyCols:
            colsAndVal[key] = data[key]
        self._secondColsAndValues = colsAndVal


class AbstractLinkTableManager(AbstractItemManager):
    _firstManager = None
    _secondManager = None

    def __init__(self, firstManager: AbstractItemManager, secondManager: AbstractItemManager):
        self._firstManager = firstManager
        self._secondManager = secondManager
        super().__init__()

    def GetPrimaryKeyColumns(self):
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        ret = []
        for fk in firstKeys:
            ret.append("first_" + fk)
        for sk in secondKeys:
            ret.append("second_" + fk)
        return ret

    def GetColumns(self):
        ret = super().GetColumns()

        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        firstCols = self._firstManager.GetColumns()
        secondCols = self._secondManager.GetColumns()

        for fk in firstKeys:
            for col in firstCols:
                if col[0] == fk:
                    ret.append(("first_" + fk, col[1]))
        for sk in secondKeys:
            for col in secondCols:
                if col[0] == sk:
                    ret.append(("second_" + sk, col[1]))
        return ret

    def FromJSONData(self, data):
        """Call the super implementation to fill AbstractLink fields first"""
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        firstQuery = []
        secondQuery = []
        for fk in firstKeys:
            firstQuery.append(fk, data["first_" + fk])
        for sk in secondKeys:
            secondQuery.append(sk, data["second_" + sk])
        l = self.NewAbstractLink()
        l._firstColsAndValues = firstQuery
        l._secondColsAndVAlues = secondQuery
        return l

    @abc.abstractmethod
    def NewLink(self) -> AbstractLink:
        """Implement this by creating a link of the specific type needed by this manager and return it."""
        raise NotImplementedError()

    def NewLinkFromParameters(self, first, second) -> AbstractLink:
        """Override this and call super to create with more data"""
        ret = self.NewLink()
        ret._setFirst(first)
        ret._setSecond(second)
        return ret

    def ToJSONData(self, item: AbstractLink):
        """Call the super() to fill AbstractLink fields first"""
        ret = []
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        for fk in firstKeys:
            ret["first_" + fk] = item._firstColsAndValues[fk]
        for sk in secondKeys:
            ret["second_" + sk] = item._secondColsAndValues[sk]
        return ret

    def GetByFirst(self, item, conn: fiepipelib.assetdata.data.connection.Connection):
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        data = self._firstManager.ToJSONData(item)
        colsAndVals = []
        for fk in firstKeys:
            colsAndVals["first_" + fk] = data[fk]
        return self._Get(conn.GetDBConnection, colsAndVals)

    def GetBySecond(self, item, conn: fiepipelib.assetdata.data.connection.Connection):
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        data = self._secondManager.ToJSONData(item)
        colsAndVals = []
        for sk in secondKeys:
            colsAndVals["second_" + sk] = data[sk]
        return self._Get(conn.GetDBConnection, colsAndVals)

    def Delete(self, link: AbstractLink, conn: fiepipelib.assetdata.data.connection.Connection):
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        colsAndVals = []
        for fk in firstKeys:
            colsAndVals["first_" + fk] = link._firstColsAndValues[fk]
        for sk in secondKeys:
            colsAndVals["second_" + sk] = link._secondColsAndValues[sk]
        self._DeleteByMultipleAND(conn.GetDBConnection(), colsAndVals)

    def DeleteByFirst(self, item, conn: fiepipelib.assetdata.data.connection.Connection):
        firstKeys = self._firstManager.GetPrimaryKeyColumns()
        data = self._firstManager.ToJSONData(item)
        colsAndVals = []
        for fk in firstKeys:
            colsAndVals["first_" + fk] = data[fk]
        self._DeleteByMultipleAND(conn.GetDBConnection(), colsAndVals)

    def DeleteBySecond(self, item, conn: fiepipelib.assetdata.data.connection.Connection):
        secondKeys = self._secondManager.GetPrimaryKeyColumns()
        data = self._secondManager.ToJSONData(item)
        colsAndVals = []
        for sk in secondKeys:
            colsAndVals["second_" + sk] = data[sk]
        self._DeleteByMultipleAND(conn.GetDBConnection(), colsAndVals)

    def CullMissing(self, conn: fiepipelib.assetdata.data.connection.Connection):
        """Culls entries that point to nothing.  A maintnance function. Shouldn't be
        called regularly.
        """
        # probably could do this better.  we're getting first and second too often. [shrug]
        allLinks = self.GetAll(conn)
        toDelete = []
        for link in allLinks:
            assert isinstance(link, AbstractLink)
            if len(link.GetFirst(conn)) == 0:
                toDelete.append(link)
            elif len(link.GetSecond(conn)) == 0:
                toDelete.append(link)
        for link in toDelete:
            self.Delete(link, conn)
