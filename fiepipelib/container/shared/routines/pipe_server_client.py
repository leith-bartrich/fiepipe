import typing

import fiepipelib.container
import fiepipelib.fiepipeserver
from fiepipelib.container.shared.routines.manager import AbstractContainerManagementRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines


class ContainerPipeServerRoutines(object):

    _container_manager_routines: AbstractContainerManagementRoutines = None

    def __init__(self, container_manager_routines:AbstractContainerManagementRoutines):

        self._container_manager_routines = container_manager_routines

    def _get_fie_pipe_server_client(self, hostname: str, username: str = None):
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        clnt = fiepipelib.fiepipeserver.client.client(hostname, username, user, False)
        return clnt

    async def pull_all_routine(self, hostname: str, username: str = None):
        """Pulls containers from the given server for the current FQDN.
        All local containers in conflict will be overwritten.
        Therefore, the remote server had better be authoritative.


        param username: the username to use to log into the host.

        param hostname: the hostname or ipaddress of a server from which to pull

        e.g. pull_all me@computer.machine.org
        e.g. pull_all server.mycompany.com
        """
        clnt = self._get_fie_pipe_server_client(hostname, username)

        connection = clnt.getConnection()
        containers = clnt.get_registered_containers_by_fqdn(connection, self._container_manager_routines.GetFQDN())
        clnt.returnConnection(connection)
        clnt.close()
        registry = self._container_manager_routines.GetManager()
        registry.Set(containers)

    async def push_all_routine(self, hostname: str, username: str = None):
        """Pushes all containers for this FQDN to the given server.
        Will overwrite all conflicting containers on the server.
        Therefore, this machine had better be authoritative.


        param username: the username to use to log into the host.

        param hostname: the hostname or ipaddress of a server to push up to.

        e.g. push_all me@computer.machine.org
        e.g. push_all server.mycompany.com
        """
        registry = self._container_manager_routines.GetManager()
        containers = registry.GetByFQDN(self._container_manager_routines.GetFQDN())
        clnt = self._get_fie_pipe_server_client(hostname, username)
        connection = clnt.getConnection()
        clnt.set_registered_containers(connection, containers)
        clnt.returnConnection(connection)
        clnt.close()

    async def pull_routine(self, hostname: str, names: typing.List[str], username: str = None):
        """Pulls containers from the given server.
        Only named containers are pulled, but those in conflict will be overwritten.
        Therefore, the remote server had better be authoritative for those named containers.
        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server from which to pull.

        param names: list of either the name or id of the containers to pull.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. pull me@computer.machine.org bigcontainer
        e.g. pull server.mycompany.com bigcontainer mediumcontainer
        """
        clnt = self._get_fie_pipe_server_client(hostname, username)
        connection = clnt.getConnection()
        containers = clnt.get_all_registered_containers(connection)
        clnt.returnConnection(connection)
        clnt.close()
        toSet = []
        for token in names:
            for cont in containers:
                doSet = False
                assert isinstance(cont, fiepipelib.container.shared.data.container.Container)
                if (cont.GetShortName() == token) and (cont.get_fqdn() == self._container_manager_routines.GetFQDN()):
                    doSet = True
                if (doSet == False) and (cont.GetID() == token):
                    doSet = True
                if doSet:
                    toSet.append(cont)
        registry = self._container_manager_routines.GetManager()
        registry.Set(toSet)

    async def push_routine(self, hostname: str, names: typing.List[str], username: str = None):
        """Pushes containers to the given server.
        Only named containers are pushed, but those in conflict will be overwritten.
        Therefore, this machine had better be authoritative for those named containers.

        param user: the username to use to log into the host.

        param host: the hostname or ipaddress of a server to push to.

        param name|id: either the name or id of the containers to push.
        those that fail to match on name will fail over to matching on ID.
        You can speficy multiple containers separated by spaces here.

        e.g. push me@computer.machine.org bigcontainer
        e.g. push server.mycompany.com bigcontainer mediumcontainer
        """
        registry = self._container_manager_routines.GetManager()
        containers = []
        for token in names:
            gotten = registry.GetByShortName(token, self._container_manager_routines.GetFQDN())
            if len(gotten) == 0:
                gotten = registry.GetByID(token)
            if len(gotten) != 0:
                await self._container_manager_routines.get_feedback_ui().feedback("Found container: " + token)
                containers.append(gotten[0])
        if len(containers) == 0:
            await self._container_manager_routines.get_feedback_ui().feedback("No containers found.  Not pushing.")
            return
        clnt = self._get_fie_pipe_server_client(hostname, username)
        connection = clnt.getConnection()
        containers = clnt.set_registered_containers(connection, containers)
        clnt.returnConnection(connection)
        clnt.close()