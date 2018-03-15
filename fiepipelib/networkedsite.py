import fiepipelib.abstractsite
import fiepipelib.registeredlegalentity

def FromJSONData(data):
    ret = networkedsite()
    fiepipelib.abstractsite.FromJSONData(ret,data)
    ret._stateServer = data['state_server']
    ret._port = data['port']
    
    return ret

def ToJSONData(site):
    assert isinstance(site, networkedsite)
    ret = {}
    fiepipelib.abstractsite.ToJSONData(site,ret)
    ret['state_server'] = site._stateServer
    ret['port'] = site._port
    
    return ret

def FromParameters(name, fqdn, stateServer, port, publicKey):
    ret = networkedsite()
    fiepipelib.abstractsite.FromParameters(ret,name,fqdn)
    ret._stateServer = stateServer
    ret._port = port
    return ret


class localregistry(fiepipelib.abstractsite.abstractlocalregistry):

    def FromJSONData(self, data):
        return FromJSONData(data)

    def ToJSONData(self, item):
        return ToJSONData(item)

    def GetManagedTypeName(self):
        return "networked_site"


class networkedsite(fiepipelib.abstractsite.abstractsite):
    """The static configuration of networked a site.  Typically created and maintained
    by a user. Often, pulled from system to system by the user.

    This is mostly public information within the entity.  And sometimes, might
    even be generally public.
    
    There is no need to sign or verify this configuration.  The actual
    verification takes place when this information is used to log into the
    state server, which must prove that it is authorized by the
    authoredlegalentity.

    In this way, we avoid trusting DNS or local network configuration, which might be used
    to spoof the site's state server.
    """

    _stateServer = None
    _port = None
    _username = None

    def GetStateServer(self):
        """Returns the hostname or ip address of the state server
        """
        return self._stateServer

    def GetPort(self):
        """Returns the port of the state server
        """
        return self._port

    def SetUsername(self, username):
        """Sets the username to use to log into the state server"""
        self._username = username

    def GetUsername(self):
        """Gets the username to use to log into the state server"""
        return self._username
