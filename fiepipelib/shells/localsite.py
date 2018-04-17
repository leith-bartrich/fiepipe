import fiepipelib.shells.abstractsite
import fiepipelib.fiepipeserver.client
import fiepipelib.localsite
import fiepipelib.container
import fiepipelib.registeredlegalentity
import sys
import fiepipelib.applauncher.genericlauncher
import fiepipelib.shells.container

class Shell(fiepipelib.shells.abstractsite.Shell):
    """A shell for working within the local site of a legal entity on this system."""
    
    def __init__(self,localUser,entity):
        self._localSite = fiepipelib.localsite.FromParameters(entity.GetFQDN())
        super().__init__(localUser,entity)
        self.AddSubmenu(fiepipelib.shells.container.ContainersCommand(
            localUser, self), "containers", ['cnt'])
        
    def GetForkArgs(self):
        return [self._entity.GetFQDN()]
        
    def getPluginNameV1(self):
        return 'localsite'

    _localSite = None

    def GetSite(self):
        return self._localSite

    def shutdownSite(self):
        pass


if __name__ == "__main__":
    p = fiepipelib.localplatform.GetLocalPlatform()
    u = fiepipelib.localuser.localuser(p)
    registry = fiepipelib.registeredlegalentity.localregistry(u)
    entities = registry.GetByFQDN(sys.argv[1])
    entity = entities[0]
    s = Shell(u,entity)
    s.cmdloop()