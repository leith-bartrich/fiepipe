import rpyc
import fiepipelib.legalentityregistry
import fiepipelib.siteregistry
import fiepipelib.container

class server(rpyc.Service):
    
    """Server run by a user on a fiepipe system."""

    _localuser = None

    def __init__(self):
        self._localuser = fiepipelib.localuser.localuser(fiepipelib.localplatform.GetLocalPlatform())

    def exposed_get_all_registered_sites(self, fqdn):
        ret = []
        registry = fiepipelib.siteregistry.siteregistry(self._localuser)
        siteNames = registry.ListNetworkedSites(fqdn)
        for s in siteNames:
            try:
                ret.append(registry.GetNetworkedSite(fqdn,s))
            except FileNotFoundError:
                #possible the file was deleted after it was listed.  We just move on.
                pass
        return ret

    def exposed_get_all_regestered_legal_entities(self):
        ret = []
        registry = fiepipelib.legalentityregistry.legalentityregistry(self._localuser)
        entityNames = registry.ListRegisteredOnDisk()
        for e in entityNames:
            try:
                ret.append(registry.GetLegalEntityFromDisk(e))
            except FileNotFoundError:
                #possible the file was deleted after it was listed.  We just move on.
                pass
        return ret

    def exposed_get_all_registered_containers(self):
        registry = fiepipelib.container.localregistry(self._localuser)
        ret = registry.GetAll()
        return ret

    def exposed_get_registered_containers_by_fqdn(self, fqdn):
        registry = fiepipelib.container.localregistry(self._localuser)
        ret = registry.GetByFQDN(fqdn)
        return ret

    def exposed_set_registered_containers(self, containers):
        """
        Sets the passed containers.
        @param containers: a list of container objects
        """
        registry = fiepipelib.container.localregistry(self._localuser)
        registry.Set(containers)
        return

    def exposed_ping(self):
        return "pong"





