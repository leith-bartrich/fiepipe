import rpyc
import rpyc.utils
import rpyc.utils.zerodeploy
import plumbum.machines.paramiko_machine
import fiepipelib.localuser.routines.localuser

class client(object):
    """Local client for the fiepipeserver server"""

    _localUser = None
    _hostname = None
    _username = None
    _policy = None

    def __init__(self, hostname, username, localUser, autoAddHosts=False):
        """@param autoAddHosts: If true, automatically adds hosts to the list of trusted hosts if it hasn't seen them before.  If false, it rejects them.
        """
        assert isinstance(localUser, fiepipelib.localuser.routines.localuser.LocalUserRoutines)
        self._localUser = localUser
        self._hostname = hostname
        self._username = username
        self._connections = []
        if autoAddHosts:
            self._policy = plumbum.machines.paramiko_machine.paramiko.AutoAddPolicy
        else:
            self._policy = plumbum.machines.paramiko_machine.paramiko.RejectPolicy
        
    _machine = None
    _server = None
    _connections = None

    def GetHostsFilePath(self):
        return os.path.joint(self._localUser.get_pipe_configuration_dir(), "fiepipeclient_known_hosts.txt")

    def RemoveKnownHost(self):
        hosts = plumbum.machines.paramiko_machine.paramiko.HostKeys(self.GetHostsFilePath())
        if hosts.lookup(self._hostname) != None:
            hosts.pop(self._hostname)
            hosts.save(self.GetHostsFilePath())

    def getConnection(self):
        """Warning.  missing host policy is auto-add.
        The first time you connect to this thing, make sure you actually trust your DNS and network.
        Subsequent reconnections should be secure.
        """
        if len(self._connections) != 0:
            return self._connections.pop()
        else:
            if self._machine == None:
                self._machine = plumbum.machines.paramiko_machine.ParamikoMachine(host=self._hostname,user=self._username,missing_host_policy=self._policy,keyfile=self.GetHostsFilePath())
            if self._server == None:
                self._server = rpyc.utils.zerodeploy.DeployedServer(remote_machine=self._machine,server_class='fiepipelib.fiepipeserver.server.server')
            connection = self._server.connect()
            return connection

    def returnConnection(self, connection):
        if not connection.closed:
            self._connections.append(connection)

    def close(self):
        if self._server != None:
            self._server.close()
        for c in self._connections:
            c.close()
        self._connections.clear()

    def get_all_registered_sites(self, connection, fqdn):
        """Usually, this data is harmless if spoofed.  Annoying for sure, but harmless. All warnings
        about signatures should be heeded when one uses this info to connect to a site later however.
        """
        return connection.get_all_registered_sites(fqdn)

    def get_all_regestered_legal_entities(self, connection):
        """This can be a good legal entity distribution mechanism as long as the user
        knows how to verify connect securely the first time they pull.  See getConnection
        for the technical explanation.  Ultimately, the question is: do you trust the
        server you logged into originally?
        """
        return connection.get_all_regestered_legal_entities()

    def get_all_registered_containers(self, connection):
        """This can be a good container distribution mechanism as long as the user
        knows how to verify a secure connection the first time they pull.  See getConnection
        for the technical explanation.  Ultimately, the quesation is: do you trust the
        server you logged into originally?  Consider using a site statesever method instead, as
        you can validate that the legal entity trusts the state server even if you've never seen
        it before.
        """
        return connection.get_all_registered_containers()

    def get_registered_containers_by_fqdn(self, connection, fqdn):
        """See get_all_registered_containers

        @param fqdn: the fqdn to restrict the search to.
        """
        return connection.get_registered_containers_by_fqdn(fqdn)

    def set_registered_containers(self, connection, containers):
        """Sets the given cainters to the registry on the server.  Used to push containers."""
        return connection.set_registered_containers(containers)

    def ping(self, connection):
        return connection.ping()

