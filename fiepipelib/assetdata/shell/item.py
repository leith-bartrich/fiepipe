import abc
import typing

import fiepipelib.assetdata
import fiepipelib.gitstorage
import fiepipelib.shells

from fiepipelib.assetdata.data.items import AbstractItemsRelation, AbstractItemManager
from fiepipelib.assetdata.data.connection import Connection, GetConnection

class ItemShell(fiepipelib.shells.AbstractShell.AbstractShell):
    """Shell that runs under the context of a given git asset shell.
    """

    _gitAssetShell = None

    def GetAssetShell(self):
        return self._gitAssetShell

    def GetGitWorkingAsset(self):
        return self.GetAssetShell()._workingAsset

    def __init__(self, gitAssetShell: fiepipelib.gitstorage.shells.gitasset.Shell):
        self._gitAssetShell = gitAssetShell
        super().__init__()

    def getPluginNamesV1(self):
        ret = super().get_plugin_names_v1()
        ret.append('all_assetdata')
        return ret


    @abc.abstractmethod
    def GetDataPromptCrumbText(self):
        raise NotImplementedError()

    def GetBreadCrumbsText(self):
        return self.prompt_separator.join([self._gitAssetShell.GetBreadCrumbsText(), self.GetDataPromptCrumbText()])


class AbstractItemCommand(ItemShell):

    def __init__(self, gitAssetShell: fiepipelib.gitstorage.shells.gitasset.Shell):
        super().__init__(gitAssetShell)

    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append('all_typed_assetdata')
        return ret


    @abc.abstractmethod
    def do_list(self,args):
        raise NotImplementedError()

    @abc.abstractmethod
    def do_create(self,args):
        raise NotImplementedError()

    @abc.abstractmethod
    def do_delete(self,args):
        raise NotImplementedError()

    @abc.abstractmethod
    def do_enter(self,args):
        raise NotImplementedError()


class AbstractNamedItemCommand(AbstractItemCommand):

    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append('all_named_type_assetdata')
        return ret


    @abc.abstractmethod
    def GetMultiManager(self) -> AbstractItemsRelation :
        raise NotImplementedError()

    @abc.abstractmethod
    def GetManager(self, db) -> AbstractItemManager :
        raise NotImplementedError()

    def GetConnection(self) -> Connection:
        conn = GetConnection(
            self.GetGitWorkingAsset())
        return conn

    @abc.abstractmethod
    def ItemToName(self, item) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def GetItemByName(self, name, manager:AbstractItemManager, conn:Connection):
        raise NotImplementedError()

    @abc.abstractmethod
    def GetAllItems(self, manager:AbstractItemManager,conn:Connection) -> typing.List:
        raise NotImplementedError()

    def do_list(self, args):
        """Lists all items.

        Usage: list
        """
        conn = self.GetConnection()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        db.AttachToConnection( conn)

        allitems = self.GetAllItems(man,conn)
        for i in allitems:
            self.poutput(self.ItemToName(i))
        conn.Close()

    def type_complete(self,text,line,begidx,endidx):
        workingAsset = self.GetGitWorkingAsset()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        conn = self.GetConnection()
        db.AttachToConnection( conn)
        allitems = self.GetAllItems(man,conn)
        conn.Close()

        ret = []

        for i in allitems:
            name = self.ItemToName(i)
            if name.startswith(text):
                ret.append(name)

        return ret

    complete_delete = type_complete

    def do_delete(self, args):
        """Deletes the given item.

        Usage: delete [name]

        arg name: The name of the item to delete.
        """
        if args == None:
            self.perror("No name given.")
            return
        if args == "":
            self.perror("No name given.")
            return

        workingAsset = self.GetGitWorkingAsset()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        conn = self.GetConnection()
        db.AttachToConnection( conn)
        self.DeleteItem(args, man, conn)
        conn.Commit()
        conn.Close()

    @abc.abstractmethod
    def DeleteItem(self, name:str, man:AbstractItemManager, conn:Connection):
        raise NotImplementedError()

    complete_enter = type_complete

    @abc.abstractmethod
    def GetShell(self, item) -> ItemShell:
        return NotImplementedError()

    def do_enter(self, args):
        """Enters a shell for working with the given item.

        Usage: enter [name]

        arg name: The name of the item to enter.
        """
        if args == None:
            self.perror("No name given.")
            return
        if args == "":
            self.perror("No name given.")
            return

        workingAsset = self.GetGitWorkingAsset()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        conn = self.GetConnection()
        db.AttachToConnection(conn)
        item = self.GetItemByName(args,man,conn)
        conn.Close()
        shell = self.GetShell(item)
        shell.cmdloop()