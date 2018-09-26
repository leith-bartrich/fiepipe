import json
import os.path
import fiepipelib.localuser.routines.localuser

"""Module for managing ports for all kinds of services.

Well known server ports are provided as constant fields.

User services might conflict with one another if they used well known ports.
Therefore, we implement a per user lookup for such ports.
One should use GetPortForUserService in order to retrieve such a port.

Please note that succesfully getting a port for a user service doesn't guarontee the
service is running.  Rather, it guarontees that if the service is running, it's at
the given port.
"""

SERVER_STATE_PORT = 6571

def PortToPath(port, path):
    data = {}
    data['port'] = port
    f = open(path,'w')
    json.dump(data,f,indent=4)
    f.flush()
    f.close()

def PortFromPath(path):
    f = open(path)
    data = json.load(f)
    f.close()
    return data['port']

def GetPortsDir():
    configdir = localUser.get_pipe_configuration_dir()
    portsdir = os.path.join(configdir,"ports")
    return portsdir

def GetPortPath(serviceName):
    portsdir = GetPortsDir()
    path = os.path.join(portsdir,serviceName + ".json")
    return path


def GetPortForUserService(localUser,serviceName):
    """Gets the last port logged by this user service when launched.  If the service is running, it's on this port.
    May raise all kinds of exceptions.  In which case, there likey isn't a running service."""
    assert isinstance(localUser, fiepipelib.localuser.routines.localuser.LocalUserRoutines)
    path = GetPortPath(serviceName)
    return PortFromPath(path)

def SetPortForUserService(localUser,serviceName, port):
    """Used to log a port for a user service.  When a service is launched, it should log its port so clients can find it.
    If exceptions are raised, the service probably should fail and log as such."""
    assert isinstance(localUser, fiepipelib.localuser.routines.localuser.LocalUserRoutines)
    path = GetPortPath(serviceName)
    PortToPath(port,path)

