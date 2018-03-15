import fiepipelib.localuser
import fiepipelib.registeredlegalentity
import fiepipelib.abstractsite
import fiepipelib.shells
import fiepipelib.shells.container

class Shell(fiepipelib.shells.abstract.Shell):
    """A shell for working in an abstract site."""

    prompt = "pipe/entity/site>"
    _localUser = None
    _entity = None

    def __init__(self, localUser, entity):
        super().__init__()
        assert isinstance(localUser,fiepipelib.localuser.localuser)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        self._localUser = localUser
        self._entity = entity
        site = self.GetSite()
        assert isinstance(site, fiepipelib.abstractsite.abstractsite)
        siteName = site.GetName()
        self.prompt = "pipe/" + entity.GetFQDN() + "/" + siteName + ">"

    def GetSite(self):
        raise NotImplementedError()

    def postloop(self):
        return super().postloop()
        self.shutdownSite()

    def shutdownSite(self):
        raise NotImplementedError()

    def container_list_completion(self, text, line, begidx, endidx):
        ret = []
        containers = self._get_all_containers()
        for cont in containers:
            if cont.GetShortName().startswith(text):
                ret.append(cont.GetShortName())
        return ret


    def _get_all_containers(self):
        """Override this: Returns a list of all enterable containers at this moment.  Usually used for listing and completion.
        """
        raise NotImplementedError()

    def do_list_containers(self, arg):
        conts = self._get_all_containers()
        for cont in conts:
            assert isinstance(cont, fiepipelib.container.container)
            print(self.colorize(cont.GetShortName(),"green") + " - " + cont.GetDescription() + " - " + self.colorize(cont.GetID(),"blue") )

    def pre_set_container(arg):
        """Override this.  Called before getting a container from the local registry.  Use this to update or pull the container or containers in a site specific manner."""
        raise NotImplementedError()

    complete_container_shell = container_list_completion

    def do_container_shell(self, arg):
        """Enters a Shell for working within a given container.
        
        Usage: set_container [name|id]

        param name|id: Either the shortName or ID of the container to enter.  It will be looked up by name and ultimately fail over to the id.  If it can't find a
        container by the givne id, it will still launch the shell with that id.  But the shell may not be useful when set to an id that doesn't exist.
        """
        if arg == None:
            print("No name or ID given.")
            return
        if arg == "":
            print("No name or ID given.")
            return

        registry = fiepipelib.container.localregistry(self._localUser)
        containers = registry.GetByShortName(arg)
        if len(containers) == 0:
            containers = registry.GetByID(arg)
        if len(containers) == 0:
            print("Container not found.")
            return
        id = containers[0].GetID()
        fiepipelib.shells.container.Shell(id,self._localUser,self._entity,self.GetSite()).cmdloop()

    complete_csh = container_list_completion

    def do_csh(self,arg):
        """A shortcut for set_container"""
        return self.do_container_shell(arg)



