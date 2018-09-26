import fiepipelib.container.shells.manager
import fiepipelib.sites.shells.abstractsite
import fiepipelib.fiepipeserver.client
import fiepipelib.sites.data.localsite
import fiepipelib.container
import fiepipelib.legalentity.registry.data.registered_entity
import sys
import fiepipelib.applauncher.genericlauncher
import fiepipelib.container.shells.container
from fiepipelib.shells.variables.fqdn_var_command import FQDNVarCommand

class Shell(fiepipelib.sites.shells.abstractsite.Shell):
    """A shell for working within the local site of a legal entity on this system."""

    _fqdn_var_command: FQDNVarCommand = None

    def __init__(self,localUser,entity):
        self._fqdn_var_command = FQDNVarCommand(entity.get_fqdn())
        self.add_variable_command(self._fqdn_var_command,"fqdn",[],False)

        self._localSite = fiepipelib.sites.data.localsite.FromParameters(entity.get_fqdn())

        super().__init__(localUser,entity)
        self.add_submenu(fiepipelib.container.shells.manager.ContainerManagerCommand(
            self._fqdn_var_command), "containers", ['cnt'])
        
    def GetForkArgs(self):
        return [self._entity.get_fqdn()]
        
    def getPluginNamesV1(self):
        ret = super().getPluginNamesV1()
        ret.append('localsite')
        return ret
    

    _localSite = None

    def GetSite(self):
        return self._localSite

    def shutdownSite(self):
        pass


if __name__ == "__main__":
    p = fiepipelib.localplatform.GetLocalPlatform()
    u = fiepipelib.localuser.localuser(p)
    registry = fiepipelib.legalentity.registry.data.registered_entity.localregistry(u)
    entities = registry.GetByFQDN(sys.argv[1])
    entity = entities[0]
    s = Shell(u,entity)
    s.cmdloop()