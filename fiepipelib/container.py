import fiepipelib.localuser
import os.path
import json
import fiepipelib.abstractmanager
import uuid


def ContainerFromJSONData(data):
    ret = container()
    ret._id = data['id']
    ret._shortName = data['shortname']
    ret._description = data['description']
    ret._components = data['components']
    ret._fqdn = data['fqdn']
    return ret

def ContainerToJSONData(cont):
    assert isinstance(cont, container)
    ret = {}
    ret['version'] = 1
    ret['id'] = cont._id
    ret['shortname'] = cont._shortName
    ret['description'] = cont._description
    ret['components'] = cont._components
    ret['fqdn'] = cont._fqdn
    return ret

def ConfigFromJSONData(data):
    ret = localconfiguration()
    ret._id = data['id']
    ret._components = data['components']
    return ret

def ConfigToJSONData(conf):
    assert isinstance(conf, localconfiguration)
    ret = {}
    ret['version'] = 1
    ret['id'] = conf._id
    ret['components'] = conf._components
    return ret

def GenerateNewID():
    u = uuid.uuid4()
    return str(u)

def ContainerFromParameters(fqdn, id,shortname,description,components = {}):
    assert isinstance(fqdn, str)
    assert isinstance(id,str)
    assert isinstance(shortname,str)
    assert isinstance(description,str)
    assert isinstance(components, dict)
    ret = container()
    ret._fqdn = fqdn
    ret._id = id
    ret._shortName = shortname
    ret._description = description
    ret._components = components
    return ret

def ConfigFromParameters(id, components = {}):
    assert isinstance(components, dict)
    ret = localconfiguration()
    ret._id = id
    ret._components = components
    return ret

class localregistry(fiepipelib.abstractmanager.abstractlocalmanager):
    """A local registry with which to find and store containers.

    Typically, one pulls containers from other sources.  Such as state servers.

    Once they're pulled, they're usually stored locally with this registry and are therefore available to be used.
    """

    def FromJSONData(self, data):
        return ContainerFromJSONData(data)

    def ToJSONData(self, item):
        return ContainerToJSONData(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("id","text"))
        ret.append(("shortname","text"))
        ret.append(("fqdn","text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["id"]

    def GetManagedTypeName(self):
        return "container"

    def GetByShortName(self, shortName, fqdn):
        return self._Get([("shortname",shortName),("fqdn",fqdn)])

    def GetByID(self, id):
        return self._Get([("id",id)])

    def GetByFQDN(self, fqdn):
        return self._Get([("fqdn",fqdn)])

    def DeleteByID(self, id):
        self._Delete("id",id)

    def DeleteByShortName(self, fqdn, shortName):
        self._DeleteByMultipleAND([("fqdn",fqdn),("shortname",shortName)])

    def DeleteByFQDN(self, fqdn):
        self._Delete("fqdn", fqdn)

class container(object):
    """
    Common or shared configuration of a container.
  
    Typically pulled from a state server and put in the localregistry for later use.
  
    Though they can be created locally too, before they're pushed up to a state server.

    In some cases, you might export them to json files and send them via other means (e-mail, on a drive, etc).

    A container is a component container and can be used with subclasses of the abstractcomponent class.
    """

    _id = None

    def GetID(self):
        """The unique ID of the container for tracking purposes.  Usually a string representation of a UUID"""
        return self._id

    _shortName = None

    def GetShortName(self):
        """A short name with which to identify this container on a working disk, in commands or other human readable listings.  Should be a single, crossplatform lowercase string with no white space."""
        return self._shortName

    _description = None

    def GetDescription(self):
        """A medium length string based description of this container, to help make it easily understood by those who encounter it."""
        return self._description

    _components = None

    def __init__(self):
        self._components = {}

    _fqdn = None

    def GetFQDN(self):
        """The FQDN to which this container belongs."""
        return self._fqdn


    def GetLocalConfiguration(self, localmanager, raiseOnNotFound = False):
        """Gets a local configuration for this container.  If there is none, it will create a new, suitable and empty one.
        
        @param localmanager: a localconfigurationmanager with which to do the searching and loading.
        """
        assert isinstance(localmanager, localconfigurationmanager)
        configs = localmanager.GetByContainer(self)
        if len(configs) == 0:
            if raiseOnNotFound:
                raise LocalConfigurationNotFoundError()
            else:
                return ConfigFromParameters(self.GetID())
        else:
            return configs[0]
            


class ComponentNotFoundError (Exception):
    pass

class LocalConfigurationtNotFoundError (Exception):
    pass

class abstractcomponent(object):
    """A base class for components that serialize to objects that contain components in a _components field.
       The _components field should contain a dictionary.  It shoudld have string keys.  The values
       should be JSON Data (dicts from the json module)"""

    _container = None 

    def __init__(self, cont):
        assert hasattr(cont,"_components")
        assert isinstance(cont._components,dict)
        self._container = cont

    def GetComponentName(self):
        """Override this.  Returns the name of the component for use in storage operations in the container's _components dict."""
        raise NotImplementedError()

    def _HasComponentJSONData(self, name):
        assert isinstance(name, str)
        return name in self._container._components.keys()

    def _GetComponentJSONData(self, name):
        assert isinstance(name, str)
        ret = self._container._components[name]
        assert isinstance(ret, dict)
        return ret

    def _SetComponentJSDONData(self, name, data):
        assert isinstance(name, str)
        assert isinstance(data, dict)
        self._container._components[name] = data
    
    def _RemoveComponentJSONData(self, name, raiseOnNotFound = False):
        assert isinstance(name, str)
        if raiseOnNotFound:
            self._container._components.pop(name)
        else:
            self._container._components.pop(name, d = {})

    def Exists(self):
        """Returns true if this component has stored data in the container."""
        return self._HasComponentJSONData(self.GetComponentName())

    def Commit(self):
        """Writes data to container."""
        data = self.SerializeJSONData()
        self._SetComponentJSDONData(self.GetComponentName(),data)

    def Clear(self):
        """Clears data from container."""
        self._RemoveComponentJSONData(self.GetComponentName(),False)

    def Load(self):
        """Loads data from container if it exists."""
        if self.Exists():
            data = self._GetComponentJSONData(self.GetComponentName())
            self.DeserializeJSONData(data)

    def DeserializeJSONData(self, data):
        """Override this and call the super.  Populates fields from the given JSON data."""
        pass

    def SerializeJSONData(self):
        """Override this and call the super.  Saves JSON data."""
        return {}

class localconfiguration(object):

    _id = None

    def GetID(self):
        return self._id

    _components = None

    def __init__(self):
        self._components = {}

class localconfigurationmanager(fiepipelib.abstractmanager.abstractlocalmanager):

    def FromJSONData(self, data):
        return ConfigFromJSONData(data)

    def ToJSONData(self, item):
        return ConfigToJSONData(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("id","text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["id"]

    def GetManagedTypeName(self):
        return "containerlocalconfiguration"

    def GetByID(self, id):
        return self._Get([("id",id)])

    def GetByContainer(self, cont):
        assert isinstance(cont, container)
        ret = self.GetByID(cont.GetID())
        return ret

    def DeleteByID(self, id):
        self._Delete("id",id)

    def DeleteByContainer(self, cont):
        assert isinstance(cont, container)
        self.DeleteByID(cont.GetID())

