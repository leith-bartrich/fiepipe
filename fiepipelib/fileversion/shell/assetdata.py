import abc
import asyncio
import pathlib

import fiepipelib.assetdata
import fiepipelib.gitstorage
from fiepipelib.assetdata.routines import VersionUpViaFileCopy, INGEST_MODE_MOVE, INGEST_MODE_COPY, IngestFileToVersion, \
    EnsureDeleteFile, DeployeTemplateRoutine
from fiepipelib.assetdata.shell.item import AbstractNamedItemCommand, ItemShell
from fiepipelib.assetdata.data.items import AbstractItemManager,AbstractItemsRelation
from fiepipelib.assetdata.data.connection import Connection, GetConnection
from fiepipelib.fileversion.data.fileversion import AbstractFileVersionManager, AbstractFileVersion
class AbstractSingleFileVersionCommand(AbstractNamedItemCommand):

    _templates = None

    def __init__(self, gitAssetShell: fiepipelib.gitstorage.shells.gitasset.Shell):
        templateType = self.GetTemplateType()
        self._templates = fiepipelib.assetdata.filetemplates.GetTemplates(templateType,
                                                                          gitAssetShell._entity.get_fqdn())
        super().__init__(gitAssetShell)

    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append('all_single_file_version_assetdata')
        return ret


    @abc.abstractmethod
    def GetFileExtension(self) -> str:
        raise NotImplementedError()

    def GetItemByName(self, name,
                     manager:AbstractFileVersionManager,
                     conn:Connection) -> AbstractFileVersion:
        return super().GetItemByName(name,manager,conn)

    def ItemToName(self, item:AbstractFileVersion):
        return item.GetVersion()

    def IsFiletype(self, p:str):
        path = pathlib.Path(p)
        ext = path.name.split('.')[-1]
        return str(ext).lower() == self.GetFileExtension().lower()

    def filetype_path_complete(self,text,line,begidx,endidx):
        possible = self.path_complete(text, line, begidx, endidx)
        ret = []
        for p in possible:
            path = pathlib.Path(p)
            if path.is_file():
                if self.IsFiletype(p):
                    ret.append(p)
            else:
                ret.append(p)
        return ret

    #@abc.abstractmethod
    #def GetVersionedUp(self, oldVer:fiepipelib.assetdata.abstractassetdata.AbstractFileVersion, newVerName:str) ->  fiepipelib.assetdata.abstractassetdata.AbstractFileVersion:
        #raise NotImplementedError()

    def complete_version_up(self,text,line,begidx,endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                      {1:self.type_complete})

    def do_version_up(self, args):
        """Versions up an existing version to a new version.  Copies the old file to the
        new file if it exists.

        Usage: version_up [oldver] [newver]

        arg oldver: the existing version
        arg newver: the name of the new version to create

        Will fail if the new version already exists.  Will not copy
        the file if the new file already exists.
        """

        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No old version given.")
            return
        if len(args) == 1:
            self.perror("No new version given.")
            return

        conn = GetConnection(self.GetGitWorkingAsset())
        db = self.GetMultiManager()
        man = self.GetManager(db)
        db.AttachToConnection(conn)

        oldver = self.GetItemByName(args[0], man, conn)

        try:
            self.do_coroutine(VersionUpViaFileCopy(oldver, args[1], man, conn, self.get_feedback_ui()))
            conn.Commit()
            conn.Close()
        except asyncio.CancelledError:
            self.pfeedback("User canceled.")
            return


    def complete_file_ingest(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                  {1:self.type_complete(text, line, begidx, endidx),
                                   2:self.path_complete( text, line, begidx, endidx),
                                   3:['copy','move']})

    def do_file_ingest(self, args):
        """Ingests the given file to the given version.  Will rename and move the file appropriately.

        Usage: file_ingest [version] [path] [mode]

        arg version: the version to ingest to

        arg path:  Path to the file.

        arg mode: 'c' or 'm' for copy or move modes.

        Will error if the file is of the wrong type or if there is already a file in-place.
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No version name given")
            return

        if len(args) == 1:
            self.perror("No path given.")
            return

        if len(args) == 2:
            self.perror("No mode given.")
            return

        conn = self.GetConnection()
        db = self.GetMultiManager()
        db.AttachToConnection(conn)
        man = self.GetManager(db)

        item = self.GetItemByName(args[0], man, conn)

        conn.Close()

        source = pathlib.Path(args[1]).absolute()

        if not self.IsFiletype(str(source)):
            self.perror("Wrong filetype.")
            return

        mode = None
        if args[2].lower() == 'move':
            mode = INGEST_MODE_MOVE
        elif args[2].lower() == 'copy':
            mode = INGEST_MODE_COPY

        try:
            self.do_coroutine(IngestFileToVersion(args[1], item, mode, self.get_feedback_ui()))
        except asyncio.CancelledError as ce:
            self.pfeedback("User Canceled.")
            return



    def complete_file_delete(self, text, line, begidx, endidx):
        return self.type_complete(text, line, begidx, endidx)

    def do_file_delete(self, args):
        """Deletes the file for the given version

        Usage: file_delete [version]

        arg version: The version to delete the file from
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No version given.")
            return

        conn = self.GetConnection()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        db.AttachToConnection( conn)

        version = self.GetItemByName(args[0], man, conn)

        conn.Close()

        try:
            self.do_coroutine(EnsureDeleteFile(version, self.get_feedback_ui()))
        except asyncio.CancelledError as ce:
            self.pfeedback("User canceled.")
            return

    def GetTemplateType(self) -> str:
        """By default, returns the same as GetFileExtension.
        Override this if you need it to be something different, or more specific.
        e.g. mb is maya's file format
        but mb.char might be a mb with a character in it
        and mb.env might be a mb with an environment in it
        """
        return self.GetFileExtension()

    def do_template_list(self, args):
        """Lists available templates.

        Usage: template_list"""

        for k in self._templates.keys():
            self.poutput(k)

    def template_complete(self, text, line, begidx, endidx):
        ret = []
        for k in self._templates.keys():
            if k.startswith(text):
                ret.append(k)
        return ret


    def complete_template_deploy(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                  {1:self.template_complete,2:self.type_complete})

    def do_template_deploy(self, args):
        """Deploys a template to a version.

        Usage: deploy_template [name] [version]

        arg name: The name of the template to deploy
        arg version: The version to deploy to.

        Will fail if the version already has a file.
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No template specified.")
            return

        if len(args) == 1:
            self.perror("No version specified.")
            return

        if args[0] not in self._templates.keys():
            self.perror("Template not found.")
            return

        templatePath = pathlib.Path(self._templates[args[0]])

        conn = self.GetConnection()
        db = self.GetMultiManager()
        db.AttachToConnection( conn)
        man = self.GetManager(db)

        version = self.GetItemByName(args[1],man,conn)

        conn.Close()

        try:
            DeployeTemplateRoutine(version, templatePath, self.get_feedback_ui())
        except asyncio.CancelledError as ce:
            self.pfeedback("User canceled.")
            return


class AbstractSingleFileVersionShell(ItemShell):

    _version = None

    def __init__(self, gitAssetShell: fiepipelib.gitstorage.shells.gitasset.Shell, version:AbstractFileVersion):
        self._version = version
        super().__init__(gitAssetShell)

    def GetVersion(self):
        return self._version

    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append("all_single_file_version_shell")
        return ret