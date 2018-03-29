import fiepipelib.localuser
import fiepipelib.shells.abstract
import fiepipelib.shells.localsite
#import fiepipelib.shells.networkedsite
import fiepipelib.applauncher.genericlauncher
import sys


class Shell(fiepipelib.shells.abstract.Shell):
    """Shell for working within a legal entity."""

    prompt = "pipe/entity>"
    _localUser = None
    _fqdn = None

    _entity = None
    """Almost always should use the private _getEntity method instead."""

    def getPluginNameV1(self):
        return 'legalentity'

    def _getEntity(self):
        
        if self._entity == None:
            print ("The entity isn't loaded.  You can try using the 'reload' command. ")
            raise RuntimeError("entity not loaded.")
        assert isinstance(self._entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        return self._entity

    def __init__(self, fqdn, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        super().__init__()
        self._localUser = localUser
        self._fqdn = fqdn
        self.prompt = "pipe/" + fqdn + ">"
        self.do_reload("")

    def do_reload(self, arg):
        """reloads the entity from disk"""
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = registry.GetByFQDN(self._fqdn)
        if len(entities) > 0:
            entity = entities[0]
            assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
            self._entity = entity
        else:
            print ("The entity doesn't exist.  Cannot load it.  You probably need to exit this shell.")
            self._entity = None

#    def do_list_networked_sites(self, arg):
#        registry = fiepipelib.networkedsite.localregistry(self._localUser)
#        entity = self._getEntity()
#        sites = registry.GetByFQDN(self._fqdn)
#        for s in sites:
#            assert isinstance(s, fiepipelib.networkedsite.networkedsite)
#            print(s.GetName())

 #   def do_delete_networked_site(self,arg):
 #       """Deletes the named networked site.
 #       Usage: delete_networked_site [sitename]
 #       arg sitename: the name of the site to delete
 #       """
 #       if arg == None:
 #           print("No sitename specified.")
 #           return
 #       if arg == "":
 #           print("No sitename specified.")
 #           return
 #       registry = fiepipelib.networkedsite.localregistry(self._localUser)
 #       fqdn = self._fqdn
 #       registry.DeleteByFQDNAndName(fqdn,arg)

#    def do_set_networked_site(self, arg):
#        raise NotImplementedError()

    def do_local_site_shell(self, arg):
        """Runs a subshell for working with the local site
        Usage: set_local_site"""
        fiepipelib.shells.localsite.Shell(self._localUser,self._getEntity()).cmdloop()

    def do_lssh(self, arg):
        """Alias for set_local_site"""
        self.do_local_site_shell(arg)

    def GetForkArgs(self):
        return [self._fqdn]

        

    #def do_add_networked_site(self,arg):
    #    """Allows the manual addition of a site.
    #    Usage: add_site [fqdn] [sitename] [stateserver]...
    #    arg fqdn: The fully qualified domain name of the legal enity to create a site in.
    #    arg sitename: The name of the site to add.
    #    arg stateserver: 1 or more servers to log into to get the state of the site.  They should be listed in failover order with the first being the primary.
    #    Example: add_site mysite.com global fiepipe1.mysite.com fiepipe2.mysite.com
    #    """
    #    if arg == None:
    #        print ("No arguments specified.")
    #        return
    #    if arg == "":
    #        print ("No arguments specified.")
    #        return
    #    args = arg.split(1)
    #    if len(args) != 2:
    #        print ("No sitename specified.")
    #        return
    #    fqdn = args[0]
    #    args = args[1].split(1)
    #    if len(args) != 2:
    #        print("No stateserver specified")
    #        return
    #    sitename = args[0]
    #    stateServers = args[1].split()
    #    site = fiepipelib.networkedsite.FromParameters(sitename,fqdn,stateServers)
    #    registery = fiepipelib.siteregistry.siteregistry(self._localUser)
    #    registery.SetNetworkedSite(site)
    #    if isinsatnce(self, fiepipelib.shells.networkedsite.Shell):
    #       self.do_reload(None)


if __name__ == "__main__":
    p = fiepipelib.localplatform.GetLocalPlatform()
    u = fiepipelib.localuser.localuser(p)
    s = Shell(sys.argv[1], u)
    s.cmdloop()