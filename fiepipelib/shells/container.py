import fiepipelib.shells.abstract
import fiepipelib.gitstorage.root
import fiepipelib.gitstorage.workingroot
import fiepipelib.gitstorage.asset
import fiepipelib.gitstorage.workingasset
import fiepipelib.registeredlegalentity
import fiepipelib.shells.gitroot
import os.path
import os

class Shell(fiepipelib.shells.abstract.Shell):
    """A shell for working in a local container"""

    def getPluginNameV1(self):
        return 'container'


    _id = None

    _localUser = None
    _entity = None
    _site = None
    
    _container = None

    prompt = "pipe/entity/site/container>"

    def root_completion(self,text,line,begidx,endidx):
        ret = []
        container = None
        try:
            container = self._GetContainer()
        except RuntimeError:
            return []
        component = fiepipelib.gitstorage.root.workingdirectoryroots(container)
        component.Load()
        roots = component.GetRoots()
        for r in roots:
            assert isinstance(r, fiepipelib.gitstorage.root.root)
            if r.GetName().startswith(text):
                ret.append(r.GetName())
            if r.GetID().lower().startswith(text.lower()):
                ret.append(r.GetID())
        return ret

    def __init__(self, id, localUser, entity, site):
        super().__init__()
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        assert isinstance(site, fiepipelib.abstractsite.abstractsite)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        self._localUser = localUser
        self._id = id
        self._site = site
        self._entity = entity
        self._ReloadContainer()

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
        self.prompt = "pipe/" + self._entity.GetFQDN() +  "/" + self._site.GetName() + "/" + self._container.GetShortName() + ">"

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

    def _DeleteConfig(self):
        manager = fiepipelib.container.localconfigurationmanager(self._localUser)
        manager.DeleteByID(self._id)


    def _GetRoot(self, nameorid):
        container = self._GetContainer()
        assert isinstance(container,fiepipelib.container.container)
        component = fiepipelib.gitstorage.root.workingdirectoryroots(container)
        component.Load()
        roots = component.GetRoots()
        root = None
        for r in roots:
            assert isinstance(r, fiepipelib.gitstorage.root.root)
            if r.GetName() == nameorid:
                root = r
            elif r.GetID() == nameorid:
                root = r
            if root != None:
                break
        if root == None:
            raise LookupError(nameorid)
        return root


    def _GetRootConfig(self, id):
        config = self._GetLocalConfig()
        configcomponent = fiepipelib.gitstorage.workingroot.localworkingdirectoryroots(config)
        configcomponent.Load()
        configuredroots = configcomponent.GetRoots()
        configedroot = None
        for c in configuredroots:
            assert isinstance(c, fiepipelib.gitstorage.workingroot.workingroot)
            if c.GetID() == id:
                configedroot = c
            if configedroot != None:
                break
        if configedroot == None:
            raise LookupError(id)
        return configedroot

    def _SetRootConfig(self, configuredroot):
        assert isinstance(configuredroot, fiepipelib.gitstorage.workingroot.workingroot)
        config = self._GetLocalConfig()
        configcomponent = fiepipelib.gitstorage.workingroot.localworkingdirectoryroots(config)
        configcomponent.Load()
        configuredroots = configcomponent.GetRoots()
        for c in configuredroots.copy():
            assert isinstance(c, fiepipelib.gitstorage.workingroot.workingroot)
            if c.GetID() == configuredroot.GetID():
                configuredroots.remove(c)
        configuredroots.append(configuredroot)
        configcomponent.SetRoots(configuredroots)
        configcomponent.Commit()
        self._CommitConfig(config)

    def _DeleteRootConfig(self, nameorid):
        root = self._GetRoot(nameorid)
        id = root.GetID()
        config = self._GetLocalConfig()
        configcomponent = fiepipelib.gitstorage.workingroot.localworkingdirectoryroots(config)
        configcomponent.Load()
        configuredroots = configcomponent.GetRoots()
        for c in configuredroots.copy():
            assert isinstance(c, fiepipelib.gitstorage.workingroot.workingroot)
            if c.GetID() == id:
                configuredroots.remove(c)
        configcomponent.SetRoots(configuredroots)
        configcomponent.Commit()
        self._CommitConfig(config)


    def do_list_roots(self,arg):
        """Lists the roots that are configured in the container."""
        cont = self._GetContainer()
        rootscomponent = fiepipelib.gitstorage.root.workingdirectoryroots(cont)
        rootscomponent.Load()
        roots = rootscomponent.GetRoots()
        for root in roots:
            assert isinstance(root, fiepipelib.gitstorage.root.root)
            id = root.GetID()
            config = None
            try:
                config = self._GetRootConfig(id)
            except LookupError:
                pass
            line = self.colorize(root.GetName(), "green")
            if config == None:
                line = line + " - " + self.colorize("[NOT CONFIGURED]","red")
            else:
                line = line + " - vol:" + config.GetVolumeName() + " subpath:" + config.GetWorkingSubPath()
            line = line + " - " + self.colorize(root.GetDescription(),"blue")
            print(line)

    def do_create_root(self,arg):
        """Creates a root in the container.  (interactive)"""
        
        container = self._GetContainer()
        id = fiepipelib.gitstorage.root.GenerateNewID()
        name = self.AskStringDefaultQuestion("Name",container.GetShortName() + "_root")
        desc = self.AskStringQuestion("Description")
        newroot = fiepipelib.gitstorage.root.RootFromParameters(id,name,desc)
        component = fiepipelib.gitstorage.root.workingdirectoryroots(container)
        component.Load()
        roots = component.GetRoots()
        roots.append(newroot)
        component.SetRoots(roots)
        component.Commit()
        self._CommitContainer()

    complete_delete_root = root_completion

    def do_delete_root(self,arg):
        """Deletes a given root in this container.

        Usage: delete_root [name]

        arg name: The name of the root to delete.
        """
        if arg == None:
            print("No root given.")
            return
        if arg == "":
            print("No root given.")
            return

        args = arg.split()

        container = self._GetContainer()
        component = fiepipelib.gitstorage.root.workingdirectoryroots(container)
        component.Load()
        roots = component.GetRoots()
        newroots = []
        for root in roots:
            assert isinstance(root, fiepipelib.gitstorage.root.root)
            if root.GetName() not in args:
                newroots.append(root)
        component.SetRoots(newroots)
        component.Commit()
        self._CommitContainer()

    complete_configure_root = root_completion

    def do_configure_root(self, arg):
        """Does a local configuration of a given storage root.  Will reconfigure if it alreayd exists.

        Usage: configure root [name|id]

        @arg name:  The name or id of the root to configure.  It will fail over from name to ID.
        """
        if arg == None:
            print("No root given.")
            return
        if arg == "":
            print("No root given.")
            return

        container = self._GetContainer()
        root = self._GetRoot(arg)
        id = root.GetID()
        configedroot = None
        try:
            configedroot = self._GetRootConfig(id)
        except LookupError:
            configedroot = fiepipelib.gitstorage.workingroot.RootFromParameters(id,"home",os.path.join(self._entity.GetFQDN(),container.GetShortName(),root.GetName()))

        assert isinstance(configedroot, fiepipelib.gitstorage.workingroot.workingroot)

        print("Listing all configured local working volumes:")
        allLocalVolumes = fiepipelib.storage.localvolume.GetAllRegisteredLocalVolumes(self._localUser)
        allLocalVolumes.append(fiepipelib.storage.localvolume.GetHomeVolume(self._localUser))
        for vol in allLocalVolumes:
            assert isinstance(vol, fiepipelib.storage.localvolume.localvolume)
            if vol.HasAdjective(fiepipelib.storage.localvolume.CommonAdjectives.containerrole.WORKING_VOLUME):
                print ("    " + vol.GetName() + " - " + vol.GetPath() )

        volname = self.AskStringDefaultQuestion("Name of local volume",configedroot.GetVolumeName())
        configedroot._volumeName = volname
        subpath = self.AskStringDefaultQuestion("Sub Path of working directory", configedroot.GetWorkingSubPath())
        configedroot._subPath = subpath

        self._SetRootConfig(configedroot)

    complete_delete_root_configuration = root_completion

    def do_delete_root_configuration(self, arg):
        """Deletes the local configuration for the given root.

        Usage: delete_root_configuration [nameorid]

        arg nameorid: The name or id of the root.  Fails over from name to id.
        """
        if arg == None:
            print("No root given.")
            return
        if arg == "":
            print("No root given.")
            return

        self._DeleteRootConfig(arg)

    complete_root_shell = root_completion

    def do_root_shell(self, arg):
        """Enters a shell for working in the given root.  The root must be configured locally.

        Usage: root_shell [nameorid]

        arg nameorid: the name or id of the root to work in.
        """

        if arg == None:
            print("No root given.")
            return
        if arg == "":
            print("No root given.")
            return

        root = None
        config = None

        try:
            root = self._GetRoot(arg)
        except LookupError:
            print(self.colorize("Could not find a root with name or id of: " + arg,"red"))
            return

        try:
            config = self._GetRootConfig(root.GetID())
        except LookupError:
            print(self.colorize("Could not load a local configuration for root: " + root.GetName() + ".  Maybe try command: configure_root",'red'))
            return

        oldDir = os.curdir
        shell = fiepipelib.shells.gitroot.Shell(root.GetID(), self._GetContainer(), self._GetLocalConfig(), self._localUser, self._entity, self._site)
        shell.cmdloop()
        os.chdir(oldDir)

    complete_rsh = root_completion

    def do_rsh(self, arg):
        self.do_root_shell(arg)

     


        



        






