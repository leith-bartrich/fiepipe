import fiepipelib.shells.abstract
import fiepipelib.gitstorage.root
import fiepipelib.gitstorage.workingroot
import fiepipelib.gitstorage.asset
import fiepipelib.gitstorage.workingasset
import fiepipelib.registeredlegalentity
import os.path
import os
import fiepipelib.shells.localsite
import abc
import cmd2
import typing
import fiepipelib.shells.gitroot
import functools

class ContainersCommand(fiepipelib.shells.abstract.LocalManagedTypeCommand):
    """A command for working with containers"""
    
    _localSiteShell = None
    
    def __init__(self, localUser:fiepipelib.localuser.localuser,localSiteShell):
        assert isinstance(localSiteShell, fiepipelib.shells.localsite.Shell)
        self._localSiteShell = localSiteShell
        super().__init__(localUser)
        
    def getPluginNameV1(self):
        return "containers"
    
    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join([self._localSiteShell.GetBreadCrumbsText(),"containers"])
        
    def GetAllItems(self):
        return self.GetManager().GetByFQDN(self._localSiteShell._entity.GetFQDN())
    
    def GetItemByName(self, name) -> fiepipelib.container.container:
        return self.GetManager().GetByShortName(name,self._localSiteShell._entity.GetFQDN())[0]
    
    def ItemToName(self, item):
        assert isinstance(item, fiepipelib.container.container)
        return item.GetShortName()
    
    def DeleteItem(self, name:str):
        self.GetManager().DeleteByShortName(self._localSiteShell._entity.GetFQDN(),name)
    
    def GetManager(self):
        return fiepipelib.container.localregistry(self._localUser)
    
    def GetShell(self, item):
        assert isinstance(item, fiepipelib.container.container)
        ret = Shell(item.GetID(), self._localUser,
                    self._localSiteShell._entity, self._localSiteShell._localSite)
        return ret
    
    def do_create(self, arg):
        """Create a new container and put it in the local registry.

        Usage: create_container
        """
        id = fiepipelib.container.GenerateNewID()
        shortname = self.AskStringDefaultQuestion("Short Name","newcontainer")
        description = self.AskStringDefaultQuestion("Description","a new container")
        container = fiepipelib.container.ContainerFromParameters(self._localSiteShell._entity.GetFQDN(),id,shortname,description)
        registry = fiepipelib.container.localregistry(self._localUser)
        registry.Set([container])
    
    complete_delete_local_configuration = fiepipelib.shells.abstract.LocalManagedTypeCommand.type_complete
    
    def do_delete_local_configuration(self, args):
        """Deletes the local configuration for a container.
        
        Usage: delete_local_configuration [containerName]
        
        arg containerName: The name of the container to de-configure.
        """
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No container specified.")
            return
        
        manager = fiepipelib.container.localconfigurationmanager(self._localUser)
        container = self.GetItemByName(args[0])
        manager.DeleteByID(container.GetID())
    
    def _get_fiepipeserver_client(arg):
        if arg == None:
            print("No host given")
        if arg == "":
            print("No host given")
        args = arg.split('@',1)
        username = None
        hostname = None
        if len(args == 2):
            username = args[0]
            hostname = args[1]
        else:
            hostname = args[0]
        clnt = fiepipelib.fiepipeserver.client.client(hostname,username,self._localUser,False)
        return clnt

    
    def do_pull_all(self, arg):
        """Pulls containers from the given server for the current FQDN.
        All local containers in conflict will be overwritten.
        Therefore, the remote server had better be authoritative.

        Usage: pull_all {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server from which to pull

        e.g. pull_all me@computer.machine.org
        e.g. pull_all server.mycompany.com
        """
        clnt = self._get_fiepipeserver_client(arg)

        connection = clnt.getConnection()
        containers = clnt.get_registered_containers_by_fqdn(connection,self._localSiteShell._entity.GetFQDN())
        clnt.returnConnection(connection)
        clnt.close()
        toAdd = []
        registry = self.GetManager()
        registry.Set(containers)
        
    def do_push_all(self,arg):
        """Pushes all containers for this FQDN to the given server.
        Will overwrite all conflicting containers on the server.
        Therefore, this machine had better be authoritative.

        Usage: push_all {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server to push up to.

        e.g. push_all me@computer.machine.org
        e.g. push_all server.mycompany.com
        """
        registry = self.GetManager()
        containers = registry.GetByFQDN(self._localSiteShell._entity.GetFQDN())
        clnt = self._get_fiepipeserver_client(arg)
        connection = clnt.getConnection()
        clnt.set_registered_containers(containers)
        clnt.returnConnection(connection)
        clnt.close()
        
    def do_pull(self, arg):
        """Pulls containers from the given server.
        Only named containers are pulled, but those in conflict will be overwritten.
        Therefore, the remote server had better be authoritative for those named containers.

        Usage: pull {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.
        
        param host: the hostname or ipaddress of a server from which to pull.
        
        param name|id: either the name or id of the containers to pull.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. pull me@computer.machine.org bigcontainer
        e.g. pull server.mycompany.com bigcontainer mediumcontainer
        """
        if arg == None:
            print("No host given")
        if arg == "":
            print("No host given")
        args = str(arg).split(maxsplit=1)
        hostarg = args[0]
        containerTokens = []
        if len(args) > 1:
            containerTokens = args[1].split()
        clnt = self._get_fiepipeserver_client(hostarg)
        connection = clnt.getConnection()
        containers = clnt.get_all_registered_containers(connection)
        clnt.returnConnection(connection)
        clnt.close()
        toSet = []
        for token in containerTokens:
            for container in containers:
                set = False
                assert isinstance(container, fiepipelib.container.container)
                if (container.GetShortName() == token) and (container.GetFQDN() == self._entity.GetFQDN()):
                    set = True
                if (set == False) and (container.GetID() == token):
                    set = True
                if set:
                    toSet.append(container)
        registry = self.GetManager()
        registry.Set(toSet)

    def do_push(self, arg):
        """Pushes containers to the given server.
        Only named containers are pushed, but those in conflict will be overwritten.
        Therefore, this machine had better be authoritative for those named containers.

        Usage: push {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.
        
        param host: the hostname or ipaddress of a server to push to.
        
        param name|id: either the name or id of the containers to push.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. push me@computer.machine.org bigcontainer
        e.g. push server.mycompany.com bigcontainer mediumcontainer
        """
        if arg == None:
            print("No host given")
        if arg == "":
            print("No host given")
        args = str(arg).split(maxsplit=1)
        hostarg = args[0]
        containerTokens = []
        if len(args) > 1:
            containerTokens = args[1].split()
        registry = self.GetManager()
        containers = []
        for token in containerTokens:
            gotten = registry.GetByShortName(token,self._entity.GetFQDN())
            if len(gotten) == 0:
                gotten = registry.GetByID(token)
            if len(gotten) != 0:
                print("Found container: " + token)
                containers.append(gotten[0])
        if len(containers) == 0:
            print("No containers found.  Not pushing.")
            return
        clnt = self._get_fiepipeserver_client(hostarg)
        connection = clnt.getConnection()
        containers = clnt.set_registered_containers(connection,containers)
        clnt.returnConnection(connection)
        clnt.close()



class Shell(fiepipelib.shells.abstract.Shell):
    """A shell for working in a local container"""

    def getPluginNameV1(self):
        return 'container'

    _id = None

    _localUser = None
    _entity = None
    _site = None
    
    _container = None



    def __init__(self, id, localUser, entity, site):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        assert isinstance(site, fiepipelib.abstractsite.abstractsite)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        self._localUser = localUser
        self._id = id
        self._site = site
        self._entity = entity
        self._ReloadContainer()
        super().__init__()
        rootsSubmenu = RootComponentCommand(self)
        self.AddSubmenu(rootsSubmenu, "roots", [])

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join(['pipe',self._entity.GetFQDN(),self._site.GetName(),self._container.GetShortName()])

    def _GetContainer(self):
        if self._container == None:
            print ("The container isn't loaded.  You can try using the 'reload' command. ")
            raise RuntimeError("container not loaded.")
        assert isinstance(self._container, fiepipelib.container.container)
        return self._container

    def _ReloadContainer(self):
        registry = fiepipelib.container.localregistry(self._localUser)
        containers = registry.GetByID(self._id)
        if len(containers) == 0:
            raise RuntimeError("Container cannot be found.  You might need to exit this shell.")
        self._container = containers[0]
        self.prompt = self.GetBreadCrumbsText() + ">"
    

    def do_reload(self, arg):
        """Reloads the container from the local registry on disk.
        """
        self._ReloadContainer()

    def _CommitContainer(self):
        registry = fiepipelib.container.localregistry(self._localUser)
        cont = self._GetContainer()
        registry.Set([cont])

    def _GetLocalConfig(self):
        manager = fiepipelib.container.localconfigurationmanager(self._localUser)
        configs = manager.GetByID(self._id)
        ret = None
        if (len(configs) == 0):
            ret = fiepipelib.container.ConfigFromParameters(self._id)
        else:
            ret = configs[0]
        assert isinstance(ret, fiepipelib.container.localconfiguration)
        return ret

    def _CommitConfig(self, config):
        assert isinstance(config, fiepipelib.container.localconfiguration)
        manager = fiepipelib.container.localconfigurationmanager(self._localUser)
        manager.Set([config])


     
class ContainerComponentCommand(fiepipelib.shells.abstract.Shell):
    
    _containerShell = None
    
    def __init__(self, containerShell:Shell):
        self._containerShell = containerShell
        super().__init__()
    
    @abc.abstractmethod
    def GetContainerComponent(self) ->  fiepipelib.container.abstractcomponent:
        raise NotImplementedError()
    
    def Commit(self, component:fiepipelib.container.abstractcomponent):
        component.Commit()
        self._containerShell._CommitContainer()
        
class LocalContainerComponentCommand(fiepipelib.shells.abstract.Shell):
    
    _containerShell = None
    
    def __init__(self, containerShell:Shell):
        self._containerShell = containerShell
        super().__init__()
        
    @abc.abstractmethod
    def GeLocalComponent(self) -> fiepipelib.container.abstractcomponent:
        raise NotImplementedError()
    
    def Commit(self, component:fiepipelib.container.abstractcomponent):
        component.Commit()
        self._containerShell._CommitConfig(component._container)

    
#class ConfigureComponentCommand(fiepipelib.shells.abstract.Shell):
    
    #_componentCommand = None
    
    #def __init__(self, componentCommand:ContainerComponentCommand):
        #self._componentCommand= componentCommand
        #super().__init__()
        
    #@abc.abstractmethod
    #def GetConfigurationComponent(self) -> fiepipelib.container.abstractcomponent:
        #raise NotImplementedError()
    
    #def Commit(self, component:fiepipelib.container.abstractcomponent):
        #component.Commit()
        #self._componentCommand._containerShell._CommitConfig(component._container)
        
    
    
class NamedMultiContainerComponentCommand(ContainerComponentCommand):

    def named_item_complete(self,text,line,begidx,endidx):
        allItems = self.GetAllItems()
        ret = []
        for i in allItems:
            iname = self.ItemToName(i)
            if iname.startswith(text):
                ret.append(iname)
        return ret

    def GetItem(self, name):
        allItems = self.GetAllItems()
        for i in allItems:
            iname = self.ItemToName()
            if iname == name:
                return i
        raise LookupError()

    @abc.abstractmethod
    def GetAllItems(self) -> typing.List:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def ItemToName(self, item) -> str:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def do_list(self, args):
        """Lists all items in this component.
        
        Usage: list
        """
        allItems = self.GetAllItems()
        for i in allItems:
            self.poutput(self.ItemToName(i))
    
    @abc.abstractmethod
    def do_create(self, args):
        raise NotImplementedError()
    
    
    @abc.abstractmethod
    def DeleteItem(self, name):
        raise NotImplementedError()

    complete_delete = named_item_complete
    
    @abc.abstractmethod
    def do_delete(self, args):
        """Deletes the given item.
        
        Usage: delete [itemName]
        
        arg itemName: The name of the item to delete.
        """
        args = self.parseline(args)
        if len(args) == 0:
            self.perror("No item name given.")
            
        name = args[0]
        self.DeleteItem(name)
    
class ConfigurableNamedMultiContainerComponentCommand(NamedMultiContainerComponentCommand):
    
    @abc.abstractmethod
    def GetLocalComponent(self) -> fiepipelib.container.abstractcomponent:
        raise NotImplementedError()
    
    def CommitLocalComponent(self, comp:fiepipelib.container.abstractcomponent):
        comp.Commit()
        self._containerShell._CommitConfig(comp._container)
    
    @abc.abstractmethod    
    def GetLocalItem(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def DeleteLocalItem(self, name):
        raise NotImplementedError()
    

    complete_configure_local = NamedMultiContainerComponentCommand.named_item_complete
    
    @abc.abstractmethod
    def do_configure_local(self, args):
        raise NotImplementedError()
    
    complete_unconfigure_local = NamedMultiContainerComponentCommand.named_item_complete

    def do_unconfigure_local(self, args):
        """Deletes the local configuration of this item.
        
        Usage: unconfigure_local [name]
        
        arg name: The name of the item to deconfigure.
        """
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No item specified.")
            return
        self.DeleteLocalItem(args[0])
    
    
class NamedLocalMultiContainerComponentCommand(LocalContainerComponentCommand):
    

    def named_item_complete(self,text,line,begidx,endidx):
        allItems = self._componentCommand.GetAllItems()
        ret = []
        for i in allItems:
            iname = self._componentCommand.ItemToName(i)
            if iname.startswith(text):
                ret.append(iname)
        return ret


    @abc.abstractmethod
    def GetAllItems(self) -> typing.List:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def GetItem(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def do_create(self,args):
        raise NotImplementedError()
        
    @abc.abstractmethod
    def DeleteItemConfiguration(self, name):
        raise NotImplementedError()

    complete_delete = named_item_complete

    def do_delete(self, args):

        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No item given.")
            return

        self.DeleteItemConfiguration(args[0])
        
            
    
       
class EnterableConfigurableNamedMultiComponentCommand(ConfigurableNamedMultiContainerComponentCommand):

    @abc.abstractmethod
    def GetShell(self, name) -> fiepipelib.shells.abstract.Shell:
        raise NotImplementedError()

    def complete_enter(self, text, line, begidx, endidx):
        return NamedMultiContainerComponentCommand.named_item_complete(self, 
            text, 
            line, 
            begidx, 
            endidx)

    def do_enter(self, args):
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        shell = self.GetShell(args[0])
        shell.cmdloop()

class EnterableNamedMultiComponentCommand(NamedMultiContainerComponentCommand):

    @abc.abstractmethod
    def GetShell(self, name) -> fiepipelib.shells.abstract.Shell:
        raise NotImplementedError()

    def complete_enter(self, text, line, begidx, endidx):
        return NamedMultiContainerComponentCommand.named_item_complete(self, 
            text, 
            line, 
            begidx, 
            endidx)

    def do_enter(self, args):
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return
        shell = self.GetShell(args[0])
        shell.cmdloop()

    
class RootComponentCommand(EnterableConfigurableNamedMultiComponentCommand):

    def getPluginNameV1(self):
        return "gitroots_component_command"
    
    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join([self._containerShell.GetBreadCrumbsText(),"gitroots_component_command"])
    
    def GetContainerComponent(self):
        container = self._containerShell._GetContainer()
        ret = fiepipelib.gitstorage.root.workingdirectoryroots(container)
        return ret
    
    def GetLocalComponent(self):
        container = self._containerShell._GetLocalConfig()
        ret = fiepipelib.gitstorage.workingroot.localworkingdirectoryroots(container)
        return ret
    
    def ItemToName(self, item):
        assert isinstance(item, fiepipelib.gitstorage.root.root)
        return item.GetName()
    
    def GetAllItems(self):
        comp = self.GetContainerComponent()
        comp.Load()
        return comp.GetRoots()
    
    def GetItem(self, name):
        allItems = self.GetAllItems()
        for i in allItems:
            assert isinstance(i, fiepipelib.gitstorage.root.root)
            if i.GetName() == name:
                return i
        raise LookupError()
    
    def DeleteItem(self, name):
        comp = self.GetContainerComponent()
        comp.Load()
        roots = comp.GetRoots()
        toSet = []
        for r in roots:
            assert isinstance(r, fiepipelib.gitstorage.root.root)
            if not (r.GetName() == name):
                toSet.append(r)
        comp.SetRoots(toSet)
        comp.Commit()
        self._containerShell._CommitContainer()
    
    def do_create(self, args):
        """Creates a git root.  (interactive)
        
        Usage: create
        """
        container = self._containerShell._GetContainer()
        id = fiepipelib.gitstorage.root.GenerateNewID()
        name = self.AskStringDefaultQuestion("Name","root")
        desc = self.AskStringQuestion("Description")
        newroot = fiepipelib.gitstorage.root.RootFromParameters(id,name,desc)
        component = self.GetContainerComponent()
        component.Load()
        roots = component.GetRoots()
        roots.append(newroot)
        component.SetRoots(roots)
        component.Commit()
        self._containerShell._CommitContainer()
    
    def GetLocalItem(self, name):
        root = self.GetItem(name)
        id = root.GetID()
        comp = self.GetLocalComponent()
        comp.Load()
        allWorkingRoots = comp.GetRoots()
        for wr in allWorkingRoots:
            assert isinstance(wr, fiepipelib.gitstorage.workingroot.workingroot)
            if wr.GetID() == id:
                return wr
        raise LookupError()
    
    def do_configure_local(self, args):
        """Configures the root locally.
        
        Usage: configure_local [name]
        
        arg name: The name of the root to configure.
        """
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No name given.")
            return

        container = self._containerShell._GetContainer()
        root = self.GetItem(args[0])
        id = root.GetID()
        workingRoot = None
        try:
            workingRoot = self.GetLocalItem(args[0])
        except LookupError:
            workingRoot = fiepipelib.gitstorage.workingroot.RootFromParameters(id,"home",os.path.join(self._containerShell._entity.GetFQDN(),container.GetShortName(),root.GetName()))

        assert isinstance(workingRoot, fiepipelib.gitstorage.workingroot.workingroot)

        #ask questions
        #getting registered volumes is different than getting mounted volumes.  So we use the storage system directly.
        print("Listing all configured local working volumes:")
        allLocalVolumes = fiepipelib.storage.localvolume.GetAllRegisteredLocalVolumes(self._containerShell._localUser)
        allLocalVolumes.append(fiepipelib.storage.localvolume.GetHomeVolume(self._containerShell._localUser))
        for vol in allLocalVolumes:
            assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
            if vol.HasAdjective(fiepipelib.storage.localvolume.CommonAdjectives.containerrole.WORKING_VOLUME):
                print ("    " + vol.GetName() + " - " + vol.GetPath() )

        volname = self.AskStringDefaultQuestion("Name of local volume",workingRoot.GetVolumeName())
        workingRoot._volumeName = volname
        subpath = self.AskStringDefaultQuestion("Sub Path of working directory", workingRoot.GetWorkingSubPath())
        workingRoot._subPath = subpath
        
        #all information captured.  now we do the actual add.
        
        
        comp = self.GetLocalComponent()
        comp.Load()
        
        workingRoots = comp.GetRoots()
        workingRoots.append(workingRoot)

        comp.SetRoots(workingRoots)
        self.CommitLocalComponent(comp)
        
    def DeleteLocalItem(self, name):
        comp = self.GetLocalComponent()
        comp.Load()
        root = self.GetItem(name)
        id = root.GetID()
        allWorkingRoots = comp.GetRoots()
        toSet = []
        for wr in allWorkingRoots:
            assert isinstance(wr, fiepipelib.gitstorage.workingroot.workingroot)
            if not (wr.GetID() == id):
                toSet.append(wr)
        comp.SetRoots(toSet)
        self.CommitLocalComponent(comp)
    
    def complete_print(self, text, line, begidx, endidx):
        return self.named_item_complete(text, line, begidx, endidx)
    
    def do_print(self, args):
        """Prints information on the given item.
        
        Usage: print [itemName]
        
        arg itemName: The name of the item to print.
        """
        args = self.ParseArguments(args)
        if len(args) == 0:
            self.perror("No item name given.")
        r = self.GetItem(args[0])
        self.poutput("Name: " + r.GetName())
        self.poutput("ID: " + r.GetID())

        config = None
        try:
            config = self.GetLocalItem(args[0])
        except LookupError:
            pass
        if config == None:
            self.poutput(self.colorize("[NOT CONFIGURED]","red"))
        else:
            self.poutput("Volume: " + config.GetVolumeName())
            self.poutput("Sub-Path: " + config.GetWorkingSubPath())
        self.poutput("Description:")
        self.ppaged(r.GetDescription())
    
    def GetShell(self, name):
        root = self.GetItem(name)
        try:
            workingRoot = self.GetLocalItem(name)
        except LookupError:
            self.poutput("Root not configured.  Try the configure command?")
            raise
        return fiepipelib.shells.gitroot.Shell(root.GetID(), self._containerShell._GetContainer(), self._containerShell._GetLocalConfig(), self._containerShell._localUser, self._containerShell._entity, self._containerShell._site)






