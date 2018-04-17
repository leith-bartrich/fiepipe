import sys
import fiepipelib.shells
import fiepipelib.shells.localuser
import fiepipelib.shells.legalentityregistry
import fiepipelib.shells.legalentityauthority
import fiepipelib.shells.localstorage
import fiepipelib.shells.legalentity
import fiepipelib.fiepipeserver.client
import fiepipelib.shells.abstract
import fiepipelib.registeredlegalentity


class Shell(fiepipelib.shells.abstract.Shell):

    intro = 'Welcome to fiepipe.  Self documenting help command: \'help\'.'
    _localUser = None

    def getPluginNameV1(self):
        return 'fiepipe'
    
    def GetBreadCrumbsText(self):
        return "pipe"

    def registered_entities_complete(self,text,line,begidx,endidx):
        
        ret = []
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = registry.GetAll()
        for e in entities:
            if e.GetFQDN().lower().startswith(text.lower()):
                ret.append(e.GetFQDN())
        return ret
    
    def __init__(self,localUser):
        assert isinstance(localUser,fiepipelib.localuser.localuser)
        self._localUser = localUser
        super().__init__()
        self.AddSubmenu(fiepipelib.shells.legalentityregistry.Shell(localUser),
                        "legal_entity_registry", ["ler"])
        self.AddSubmenu(fiepipelib.shells.localuser.Shell(localUser), "local_user", [])
        self.AddSubmenu(fiepipelib.shells.localstorage.Shell(localUser), "local_storage", [])
        

    #def do_local_user_shell(self,arg):
        #"""Subshell for working with the local user"""
        #fiepipelib.shells.localuser.Shell(self._localUser).cmdloop()

    #def do_legal_entity_registry_shell(self,arg):
        #"""Subshell for working with the legal entity registry"""
        #fiepipelib.shells.legalentityregistry.Shell(self._localUser).cmdloop()

    #def do_local_storage_shell(self,arg):
        #"""Subshell for working with the local storage"""
        #fiepipelib.shells.localstorage.Shell(self._localUser).cmdloop()

    def do_legal_entity_authority_shell(self,arg):
        """Subshell for workign with the legal entity authority"""
        fiepipelib.shells.legalentityauthority.Shell(self._localUser).cmdloop()

    #complete_legal_entity_shell = registered_entities_complete

    #def do_legal_entity_shell(self,arg):
        #"""Subshell for working within a legal entity
        #Usage: set_legal_entity [fqdn]
        #arg fqdn: the fully qualified domain name of the legal entity to enter."""
        #if arg == None:
            #print("Must specify a fqdn.")
            #return
        #if arg == "":
            #print("Must specify a fqdn.")
            #return
        #fiepipelib.shells.legalentity.Shell(arg,self._localUser).cmdloop()

    #complete_lesh = registered_entities_complete

    #def do_lesh(self, arg):
        #"""Alias for set_legal_entity"""
        #self.do_legal_entity_shell(arg)

    def do_register_host(self, arg):
        if arg == None:
            print("No hostname given.")
            return
        if arg == "":
            print("No hostname given.")
            return
        args = arg.split(1)
        if len(args) != 2:
            print ("No username given")
            return
        #we auto add to hosts file on this request.
        #TODO: we probably need another command to de-register a host at some point.
        client = fiepipelib.fiepipeserver.client.client(args[0],args[1],True)
        connection = client.getConnection()
        client.ping(connection)
        client.returnConnection(connection)
        client.close()

    def do_remove_host(self, arg):
        if arg == None:
            print("No hostname given.")
            return
        if arg == "":
            print("No hostname given.")
            return
        client = fiepipelib.fiepipeserver.client.client(args[0],"nobody")
        client.RemoveKnownHost()
        client.close()

    #def do_pull_registered_legal_entities(self, arg):
        #"""Pulls the registered legal entities from the given server. Make sure you trust this server.
        #Usage: pull_registered_legal_entities [hostname] [username]
        #arg hostname: The hostname of the server to connect to.
        #arg username: The username to use to connect.
        #"""
        #if arg == None:
            #print("No hostname given.")
            #return
        #if arg == "":
            #print("No hostname given.")
            #return
        #args = arg.split(1)
        #if len(args) != 2:
            #print ("No username given")
            #return
        #client = fiepipelib.fiepipeserver.client.client(args[0],args[1])
        #connection = client.getConnection()
        #entities = client.get_all_regestered_legal_entities(connection)
        #client.returnConnection(connection)
        #client.close()
        #registry = fiepipelib.legalentityregistry.legalentityregistry(self._localUser)
        #for entity in entities:
            #assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
            #registry.Register(entity)

    def do_pull_known_networked_sites(self, arg):
        """Pulls the known networked sites for a legal entity from the given server.
        Usage: pull_known_networked_sites [hostname] [username] [entity]
        arg hostname: The hostname of the server to connect to.
        arg username: The username to use to connect.
        arg entity: The fully qualified domain name of the known legal entity.
        """
        if arg == None:
            print("No hostname given.")
            return
        if arg == "":
            print("No hostname given.")
            return
        args = arg.split(2)
        if len(args) < 2:
            print ("No username given.")
            return
        if len(args) != 3:
            print ("No entity given.")
        fqdn = args[2]
        client = fiepipelib.fiepipeserver.client.client(args[0],args[1])
        connection = client.getConnection()
        sites = client.get_all_registered_sites(connection,fqdn)
        client.returnConnection(connection)
        client.close()
        registry = fiepipelib.siteregistry.siteregistry(self._localUser)
        for site in sites:
            assert isinstance(site,fiepipelib.networkedsite.networkedsite)
            registry.SetNetworkedSite(site)


if __name__ == "__main__":
    p = fiepipelib.localplatform.GetLocalPlatform()
    u = fiepipelib.localuser.localuser(p)
    s = Shell(u)
    s.cmdloop()