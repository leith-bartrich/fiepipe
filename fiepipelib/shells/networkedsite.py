import fiepipelib.shells.abstractsite
import rpyc
import rpyc.utils
import rpyc.utils.zerodeploy
import plumbum.machines.paramiko_machine
import fiepipelib.stateserver
import Crypto.Random

class Shell(fiepipelib.shells.abstractsite.Shell):
    """Shell for working in a networked site."""

    _siteName
    _networkedSite = None

    def GetSite(self):
        if self._networkedSite == None:
            print("No site not loaded.  You could try the 'reload' command.")
            raise RuntimeError("Site not loaded.")
        else:
            return self._networkedSite

    def __init__(self,localUser,entity,siteName):
        super().__init__(localUser,entity)
        self._siteName = siteName
        self.do_reload(None)

    def do_reload(self, arg):
        """Reloads the named site from disk.
        Usage: reload
        """
        registry = fiepipelib.networkedsite.localregistry(self._localUser)
        fqdn = self._entity.GetFQDN()
        sites = registry.GetByFQDN(fqdn)
        self._networkedsite = None
        for site in sites:
            assert isinstance(site, fiepipelib.networkedsite.networkedsite)
            if site.GetName() == self._siteName:
                self._networkedsite = site
        if self._networkedSite == None:
            print("Site not found.  You probably need to exit this shell.")
            return

    def shutdownSite(self):
        pass






