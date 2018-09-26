import abc
import json
import os
import os.path
import pathlib
import typing

from fiepipelib.locallymanagedtypes.data.abstractmanager import AbstractUserLocalTypeManager
from fieui.FeedbackUI import AbstractFeedbackUI

T = typing.TypeVar("T")


class AbstractLocalManagedRoutines(typing.Generic[T]):
    _feedbackUI: AbstractFeedbackUI = None

    def get_feedback_ui(self) -> AbstractFeedbackUI:
        return self._feedbackUI

    def __init__(self, feedback_ui: AbstractFeedbackUI):
        self._feedbackUI = feedback_ui

    # we can't neccesarily implement the following becasue we don't have context.
    # e.g. the "project" may determine what "all" means.

    @abc.abstractmethod
    def GetManager(self) -> AbstractUserLocalTypeManager[T]:
        raise NotImplementedError()

    @abc.abstractmethod
    def GetAllItems(self) -> typing.List[T]:
        raise NotImplementedError()

    @abc.abstractmethod
    def ItemToName(self, item: T) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def GetItemByName(self, name: str) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    async def DeleteRoutine(self, name: str):
        raise NotImplementedError()

    @abc.abstractmethod
    async def CreateUpdateRoutine(self, name: str):
        raise NotImplementedError()

    async def ImportRoutine(self, path):
        """Import an item from a file
        @arg path:  The absolute path to a .json file which contains an item's JSON data."""
        path = pathlib.Path(path)
        if not path.is_absolute():
            await self.get_feedback_ui().error("filename is not an absolute path: " + str(path))
            raise IOError()
        if not path.exists():
            await self.get_feedback_ui().error("file not found: " + str(path))
            raise FileNotFoundError(str(path))
        if not path.is_file():
            await self.get_feedback_ui().error("the path does not lead to a file: " + str(path))
            raise IOError(str(path))

        data = None
        with path.open() as f:
            data = json.load(f)

        man = self.GetManager()
        entity = man.FromJSONData(data)
        await self.get_feedback_ui().feedback("found valid item at: " + str(path))
        man.Set([entity])
        await self.get_feedback_ui().feedback("registered.")

    async def ImportAllRoutine(self, path):
        """Import all items from a directory
        Usage: import [pathname]
        arg pathname:  The absolute path to a directory which contains .json files which contain item JSON data."""
        path = pathlib.Path(path)
        if not path.is_absolute():
            await self.get_feedback_ui().error("pathname is not an absolute path.")
            raise IOError()
        if not path.exists():
            await self.get_feedback_ui().error("path not found: " + str(path))
            raise FileNotFoundError((str(path)))
        if not path.is_dir():
            await self.get_feedback_ui().error("the path does not lead to a directory: " + str(path))
            raise IOError()
        files = os.listdir(str(path))
        for file in files:
            f, e = os.path.splitext(file)
            if (e.lower() == ".json"):
                await self.ImportRoutine(os.path.join(str(path), file))

    async def ExportRoutine(self, name: str, path: str):
        """Export an item to a file
        @arg path:  The absolute path to a .json file which contains an item's JSON data.
        @arg name:  The name of the item to export."""
        path = pathlib.Path(path)
        if not path.is_absolute():
            await self.get_feedback_ui().error("filename is not an absolute path: " + str(path))
            raise IOError()
        parDirPath = pathlib.Path(path.parent)
        if not parDirPath.exists():
            os.makedirs(str(parDirPath))

        item = self.GetItemByName(name)
        man = self.GetManager()
        data = man.ToJSONData(item)
        with path.open('w') as f:
            json.dump(data, f,indent=4,sort_keys=True)

        await self.get_feedback_ui().feedback("File written: " + str(path))

    async def ExportAllRoutine(self, path: str):
        """Export all items to a directory
        arg path:  The absolute path to a directory."""
        path = pathlib.Path(path)

        if not path.is_absolute():
            await self.get_feedback_ui().error("pathname is not an absolute path.")
            raise IOError()

        if not path.exists():
            os.makedirs(str(path))

        if not path.is_dir():
            await self.get_feedback_ui().error("the path does not lead to a directory: " + str(path))
            raise IOError()

        allItems = self.GetAllItems()

        for item in allItems:
            itemPath = os.path.join(str(path), self.ItemToName(item) + ".json")
            await self.ExportRoutine(self.ItemToName(item), itemPath)
