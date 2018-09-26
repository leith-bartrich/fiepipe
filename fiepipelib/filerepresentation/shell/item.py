import fiepipelib.assetdata
import fiepipelib.gitstorage
from fiepipelib.assetdata.shell.item import AbstractNamedItemCommand, ItemShell
from fiepipelib.fileversion.shell.assetdata import AbstractSingleFileVersionShell
from fiepipelib.filerepresentation.data.filerepresentation import AbstractRepresentation,AbstractRepresentationManager
from fiepipelib.assetdata.data.connection import Connection,GetConnection

class AbstractSingleFileRepresentationsCommand(AbstractNamedItemCommand):

    _versionShell = None

    def GetVersion(self):
        return self._versionShell.GetVersion()

    def GetVersionShell(self) -> AbstractSingleFileVersionShell:
        return self._versionShell

    def __init__(self, gitAssetShell: fiepipelib.gitstorage.shells.gitasset.Shell, versionShell: AbstractSingleFileVersionShell):
        self._versionShell = versionShell
        super().__init__(gitAssetShell)

    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append("all_single_file_representations_command")
        return ret

    def GetDataPromptCrumbText(self):
        return ('represenations')


    def ItemToName(self, item):
        assert isinstance(item, AbstractRepresentation)
        return item._name

    def DeleteItem(self, name:str,
                  man:AbstractRepresentationManager,
                  conn:Connection):
        man.delete_by_name(name, self._versionShell._version, conn)

    def GetItemByName(self, name,
                     manager:AbstractRepresentationManager,
                     conn:Connection) -> AbstractRepresentation:
        return manager.get_by_name(name, self._versionShell._version, conn)


class AbstractRepresentationShell(ItemShell):

    _versionShell = None
    _representation = None

    def __init__(self, versionShell: AbstractSingleFileVersionShell, representation:AbstractRepresentation):
        self._representation = representation
        self._versionShell = versionShell
        super().__init__(versionShell.GetAssetShell())

    def GetRepresentation(self) -> AbstractRepresentation:
        return self._representation

    def GetVersionShell(self) -> AbstractSingleFileVersionShell:
        return self._versionShell

    def getPluginNameV1(self):
        return "freecad_part_design_representation_shell"

    def GetBreadCrumbsText(self):
        return self.prompt_separator.join([self._versionShell.GetBreadCrumbsText(), self._representation._name])