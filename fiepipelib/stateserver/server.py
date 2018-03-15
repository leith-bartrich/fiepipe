import rpyc
import fiepipelib.localplatform
import fiepipelib.localuser
import fiepipelib.siteregistry
import fiepipelib.legalentityregistry

class server(rpyc.Service):
    """Service for the state of a networked site.
    
    Should be run by a privledged user who has access to the private key.  The private key
    should not be made available to all users on the server.

    Meant to be run on the loopback adapter and accessed by logged-in users of the system.

    Hence, security is handled by the local system's login system.  All data provided by
    this server is public to all users who can log in to this server.

    The site network's current state is managed and published from here.

    Since this is a live, threaded server, it can serve as a semaphore for the whole networked site.

    High availabiity for this server should be provided by the system itself.  Redundant or replicated
    storage, power supplies and failover are the responsibility of the system architect.

    However, the high availability of this system should provide authority to accomplish redundancy and failover to all other
    parts of the network.  In otherwords, it is the fact that this is the single point of failure and state
    of the network, that allows it to direct the rest of the network's redundancy.  Heartbeat and failover and recovery
    between other servers should be directed from here.  Hence, relieving any of those systems of needing to be highly available
    themselves.
    """

    _localuser = None
    _privatekey = None
    _fqdn = None

    def __init__(self,privatekey,fqdn):
        assert isinstance(privatekey, fiepipelib.privatekey.networkedsiteprivatekey)
        self._localuser = fiepipelib.localuser.localuser(fiepipelib.localplatform.GetLocalPlatform())
        self._privatekey = privatekey
        self._fqdn = fqdn

    #both of the verification methods below need to be used to trust this server.
    #
    #first, the public key needs to be retrieved and then signatures checked locally.
    #This verifies that the entity considers the holder of the assocaited
    #private key to be authorized to
    #be the site.
    #
    #That's not enough.  You also need to send some random (new) data from the client
    #and have it
    #signed by the private key, to verify that the server has both parts of the key
    #and can use them.

    def exposed_get_public_key(self):
        """Returns the public key, and signatures that should
           prove that it is authorized by the legal entity.  The signatures should
           be checked against an up to date legalentity that the client trusts."""
        return self._privatekey.GetPublicKey()

    def exposed_sign_message(self, msg):
        """Signs the given message with the private key.
           Which proves to anyone who holds or retrieves the public key,
           that this server actually does hold the associated private key and can use it."""
        return self._privatekey.Sign(msg,"legalentity:" + self._fqdn)

    def exposed_blah(self):
        pass


