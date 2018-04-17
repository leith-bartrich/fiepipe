import fiepipelib.shells.abstract
import fiepipelib.shells.gitasset
import abc
import typing
import pathlib
import os
import os.path
import shutil


class AssetShell(fiepipelib.shells.abstract.Shell):
    """Shell that runs under the context of a given git asset shell.
    """
    
    _gitAssetShell = None
    
    def GetAssetShell(self):
        return self._gitAssetShell
    
    def GetGitWorkingAsset(self):
        return self.GetAssetShell()._workingAsset
    
    def __init__(self,gitAssetShell:fiepipelib.shells.gitasset.Shell):
        self._gitAssetShell = gitAssetShell
        super().__init__()
        
    @abc.abstractmethod
    def GetDataPromptCrumbText(self):
        raise NotImplementedError()

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join([self._gitAssetShell.GetBreadCrumbsText(),self.GetDataPromptCrumbText()])

#class AbstractShell(fiepipelib.shells.abstract.Shell):
    
    #_gitAssetShell = None
    
    #def GetAssetShell(self):
        #return self._gitAssetShell
    
    #def GetGitWorkingAsset(self):
        #return self.GetAssetShell()._workingAsset
    
    #def __init__(self,gitAssetShell:fiepipelib.shells.gitasset.Shell):
        #self._gitAssetShell = gitAssetShell
        #super().__init__()
        
    #@abc.abstractmethod
    #def GetDataPromptCrumbText(self):
        #raise NotImplementedError()

    #def GetBreadCrumbsText(self):
        #return self.breadcrumbs_separator.join([self._gitAssetShell.GetBreadCrumbsText(),self.GetDataPromptCrumbText()])

class AbstractTypeCommand(AssetShell):
    
    def __init__(self, gitAssetShell:fiepipelib.shells.gitasset.Shell):
        super().__init__(gitAssetShell)
    
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



class AbstractNamedTypeCommand(AbstractTypeCommand):
    
    @abc.abstractmethod
    def GetMultiManager(self) -> fiepipelib.assetdata.abstractassetdata.abstractmultimanager :
        raise NotImplementedError()
    
    @abc.abstractmethod
    def GetManager(self, db) -> fiepipelib.assetdata.abstractassetdata.abstractdatamanager :
        raise NotImplementedError()
    
    def GetConnection(self) -> fiepipelib.assetdata.assetdatabasemanager.Connection:
        conn = fiepipelib.assetdata.assetdatabasemanager.GetConnection(
            self.GetGitWorkingAsset())
        return conn
    
    @abc.abstractmethod
    def ItemToName(self, item) -> str:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def GetItemByName(self, name, manager:fiepipelib.assetdata.abstractassetdata.abstractdatamanager, conn:fiepipelib.assetdata.assetdatabasemanager.Connection):
        raise NotImplementedError()

    @abc.abstractmethod
    def GetAllItems(self, manager:fiepipelib.assetdata.abstractassetdata.abstractdatamanager,conn:fiepipelib.assetdata.assetdatabasemanager.Connection) -> typing.List:
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
    def DeleteItem(self, name:str, man:fiepipelib.assetdata.abstractassetdata.abstractdatamanager, conn:fiepipelib.assetdata.assetdatabasemanager.Connection):
        raise NotImplementedError()
    
    complete_enter = type_complete
    
    @abc.abstractmethod
    def GetShell(self, item) -> AssetShell:
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
        
        
class AbstractSingleFileVersionCommand(AbstractNamedTypeCommand):
    
    
    _templates = None
    
    def __init__(self, gitAssetShell:fiepipelib.shells.gitasset.Shell):
        self._templates = {}
        super().__init__(gitAssetShell)

    def AddTemplate(self, name:str, path:str):
        self._templates[name] = path    
    
    @abc.abstractmethod
    def GetFileExtension(self) -> str:
        raise NotImplementedError()
    
    def GetItemByName(self, name, 
                     manager:fiepipelib.assetdata.abstractassetdata.abstractdatamanager, 
                     conn:fiepipelib.assetdata.assetdatabasemanager.Connection) -> fiepipelib.assetdata.abstractassetdata.AbstractFileVersion:
        return super().GetItemByName(name,manager,conn)
            
    
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
    
    @abc.abstractmethod
    def GetVersionedUp(self, oldVer:fiepipelib.assetdata.abstractassetdata.AbstractFileVersion, newVerName:str) ->  fiepipelib.assetdata.abstractassetdata.AbstractFileVersion:
        raise NotImplementedError()

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
        
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            self.perror("No old version given.")
            return
        if len(args) == 1:
            self.perror("No new version given.")
            return
        
        conn = fiepipelib.assetdata.assetdatabasemanager.GetConnection(self.GetGitWorkingAsset())
        db = self.GetMultiManager()
        man = self.GetManager(db)
        db.AttachToConnection(conn)
        
        oldver = self.GetItemByName(args[0], man, conn)
        
        if oldver == None:
            self.perror("Old version doesn't exist.")
            return

        try:
            existing = self.GetItemByName(args[1],man,conn)
            self.perror("New version already exists.")
            return
        except LookupError:
            pass
        
        newver = self.GetVersionedUp( oldver, args[1])
        
        man.Set([newver], conn)
        conn.Commit()
        conn.Close()
        
        if oldver.FileExists() & (not newver.FileExists()):
            self.poutput("Copying file...")
            shutil.copyfile(oldver.GetAbsolutePath(),
                            newver.GetAbsolutePath())
            self.poutput("Done.")
    
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
        args = self.ParseArguments(args)
        
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
        
        if item == None:
            self.perror("Version not found.")
            return        
        
        target = pathlib.Path(item.GetAbsolutePath())
        
        if target.exists():
            self.perror("File already exists.")
            return
        
        source = pathlib.Path(args[1]).absolute()
        
        if not source.is_file():
            self.perror("Not a file.")
            return
        
        if not self.IsFiletype(str(source)):
            self.perror("Wrong filetype.")
            return
        
        pardir = pathlib.Path(target.parent)
        if not pardir.exists():
            os.makedirs(str(pardir))
        
        if args[2].lower() == 'move':
            source.rename(target)
        elif args[2].lower() == 'copy':
            shutil.copyfile(str(source), str(target))
        else:
            self.perror("Unknown mode: " + args[2])
            return
        
    def complete_file_delete(self, text, line, begidx, endidx):
        return self.type_complete(text, line, begidx, endidx)
        
    def do_file_delete(self, args):
        """Deletes the file for the given version
        
        Usage: file_delete [version]
        
        arg version: The version to delete the file from
        """
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            self.perror("No version given.")
            return
        
        conn = self.GetConnection()
        db = self.GetMultiManager()
        man = self.GetManager(db)
        db.AttachToConnection( conn)
        
        version = self.GetItemByName(args[0], man, conn)
        
        conn.Close()
        
        path = pathlib.Path(version.GetAbsolutePath())
        if path.exists():
            path.unlink()
        

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
        args = self.ParseArguments(args)
        
        if len(args) == 0:
            self.perror("No template specified.")
            return
        if len(args) == 1:
            self.perror("No version specified.")
            return
        
        templatePath = pathlib.Path(self._templates[args[0]])
        
        conn = self.GetConnection()
        db = self.GetMultiManager()
        db.AttachToConnection( conn)
        man = self.GetManager(db)
        
        version = self.GetItemByName(args[1],man,conn)
        
        conn.Close()
        
        versionPath = pathlib.Path(version.GetAbsolutePath())
        
        if versionPath.exists():
            self.perror("File already exists for this version.")
            return
        
        if not templatePath.exists():
            self.perror("Template file does not exist.")
            return
        
        parentDir = pathlib.Path(versionPath.parent)
        if not parentDir.exists():
            os.makedirs(str(parentDir))
        
        self.pfeedback("Copying file...")
        shutil.copyfile(str(templatePath), str(versionPath))
        self.pfeedback("Done.")
        
