import fiepipelib.shells.abstractsite
import fiepipelib.fiepipeserver.client
import fiepipelib.localsite
import fiepipelib.container
import fiepipelib.registeredlegalentity
import sys
import fiepipelib.applauncher.genericlauncher

class Shell(fiepipelib.shells.abstractsite.Shell):
    """A shell for working within the local site of a legal entity on this system."""
    
    def __init__(self,localUser,entity):
        self._localSite = fiepipelib.localsite.FromParameters(entity.GetFQDN())
        super().__init__(localUser,entity)
        
    def GetForkArgs(self):
        return [self._entity.GetFQDN()]
        
    def getPluginNameV1(self):
        return 'localsite'

    _localSite = None

    def GetSite(self):
        return self._localSite

    def shutdownSite(self):
        pass

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

    def pre_set_container(arg):
        pass

    def do_pull_all_containers(self, arg):
        """Pulls containers from the given server for the current FQDN.
        All local containers in conflict will be overwritten.
        Therefore, the remote server had better be authoritative.

        Usage: pull_all_containers {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server from which to pull

        e.g. pull_all_containers me@computer.machine.org
        e.g. pull_all_containers server.mycompany.com
        """
        clnt = self._get_fiepipeserver_client(arg)

        connection = clnt.getConnection()
        containers = clnt.get_registered_containers_by_fqdn(connection,self._entity.GetFQDN())
        clnt.returnConnection(connection)
        clnt.close()
        toAdd = []
        registry = fiepipelib.container.localregistry(self._localUser)
        registry.Set(containers)
        
    def do_push_all_containers(self,arg):
        """Pushes all containers for this FQDN to the given server.
        Will overwrite all conflicting containers on the server.
        Therefore, this machine had better be authoritative.

        Usage: push_all_containers {[user]@}[host]

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server to push up to.

        e.g. push_all_containers me@computer.machine.org
        e.g. push_all_containers server.mycompany.com
        """
        registry = fiepipelib.container.localregistry(self._localUser)
        containers = registry.GetByFQDN(self._entity.GetFQDN())
        clnt = self._get_fiepipeserver_client(arg)
        connection = clnt.getConnection()
        clnt.set_registered_containers(containers)
        clnt.returnConnection(connection)
        clnt.close()
        
    def do_pull_containers(self, arg):
        """Pulls containers from the given server.
        Only named containers are pulled, but those in conflict will be overwritten.
        Therefore, the remote server had better be authoritative for those named containers.

        Usage: pull_containers {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.
        
        param host: the hostname or ipaddress of a server from which to pull.
        
        param name|id: either the name or id of the containers to pull.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. pull_containers me@computer.machine.org bigcontainer
        e.g. pull_all_containers server.mycompany.com bigcontainer mediumcontainer
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
        registry = fiepipelib.container.localregistry(self._localUser)
        registry.Set(toSet)

    def do_push_containers(self, arg):
        """Pushes containers to the given server.
        Only named containers are pushed, but those in conflict will be overwritten.
        Therefore, this machine had better be authoritative for those named containers.

        Usage: push_containers {[user]@}[host] [name|id] [...]

        param user: the username to use to log into the host.
        
        param host: the hostname or ipaddress of a server to push to.
        
        param name|id: either the name or id of the containers to push.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. push_containers me@computer.machine.org bigcontainer
        e.g. push_containers server.mycompany.com bigcontainer mediumcontainer
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
        registry = fiepipelib.container.localregistry(self._localUser)
        containers = []
        for token in containerTokens:
            gotten = registry.GetByShortName(token)
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

    def do_create_container(self, arg):
        """Create a new container and put it in the local registry.

        Usage: create_container
        """
        id = fiepipelib.container.GenerateNewID()
        shortname = self.AskStringDefaultQuestion("Short Name","newcontainer")
        description = self.AskStringDefaultQuestion("Description","a new container")
        container = fiepipelib.container.ContainerFromParameters(self._entity.GetFQDN(),id,shortname,description)
        registry = fiepipelib.container.localregistry(self._localUser)
        registry.Set([container])

    def _get_all_containers(self):
        registry = fiepipelib.container.localregistry(self._localUser)
        containers = registry.GetByFQDN(self._entity.GetFQDN())
        return containers

    def do_delete_containers(self, arg):
        """Deletes the containers by the given name(s) and ID(s).

        Usage: delete_containers [name|id] {...}

        arg name|id: The short name or id of the container(s) to delete, separated by spaces.

        e.g. delete_containers big_container
        e.g. delete_containers big_container medium_container
        """

        if arg == None:
            print ("No container specified.")
            return
        if arg == "":
            print("No container specified.")

        args = arg.split()
        registry = fiepipelib.container.localregistry(self._localUser)
        for token in args:
            registry.DeleteByShortName(self._entity.GetFQDN(),token)
            registry.DeleteByID(token)

if __name__ == "__main__":
    p = fiepipelib.localplatform.GetLocalPlatform()
    u = fiepipelib.localuser.localuser(p)
    registry = fiepipelib.registeredlegalentity.localregistry(u)
    entities = registry.GetByFQDN(sys.argv[1])
    entity = entities[0]
    s = Shell(u,entity)
    s.cmdloop()