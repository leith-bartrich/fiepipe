import typing
import uuid

import fiepipelib.locallymanagedtypes.data.abstractmanager


class Container(object):
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

    def GetFQDN(self) -> str:
        """The FQDN to which this container belongs."""
        return self._fqdn


def ContainerFromJSONData(data: dict) -> Container:
    ret = Container()
    ret._id = data['id']
    ret._shortName = data['shortname']
    ret._description = data['description']
    ret._components = data['components']
    ret._fqdn = data['fqdn']
    return ret


def ContainerToJSONData(cont: Container) -> dict:
    ret = {}
    ret['version'] = 1
    ret['id'] = cont._id
    ret['shortname'] = cont._shortName
    ret['description'] = cont._description
    ret['components'] = cont._components
    ret['fqdn'] = cont._fqdn
    return ret


def GenerateNewID() -> str:
    u = uuid.uuid4()
    return str(u)


def ContainerFromParameters(fqdn: str, id: str, shortname: str, description: str, components: dict = {}) -> Container:
    ret = Container()
    ret._fqdn = fqdn
    ret._id = id
    ret._shortName = shortname
    ret._description = description
    ret._components = components
    return ret


class LocalContainerManager(
    fiepipelib.locallymanagedtypes.data.abstractmanager.AbstractUserLocalTypeManager[Container]):
    """A local manager/registry with which to find and store containers.

    Typically, one pulls containers from other sources.  Such as state servers.

    Once they're pulled, they're usually stored locally with this registry and are therefore available to be used.
    """

    def FromJSONData(self, data) -> Container:
        return ContainerFromJSONData(data)

    def ToJSONData(self, item: Container) -> dict:
        return ContainerToJSONData(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("id", "text"))
        ret.append(("shortname", "text"))
        ret.append(("fqdn", "text"))
        return ret

    def GetPrimaryKeyColumns(self) -> typing.List[str]:
        return ["id"]

    def GetManagedTypeName(self) -> str:
        return "container"

    def GetByShortName(self, shortName: str, fqdn: str = '*') -> typing.List[Container]:
        if fqdn == '*':
            return self._Get([("shortname", shortName)])
        else:
            return self._Get([("shortname", shortName), ("fqdn", fqdn)])

    def GetByID(self, id: str) -> typing.List[Container]:
        return self._Get([("id", id)])

    def GetByFQDN(self, fqdn: str) -> typing.List[Container]:
        return self._Get([("fqdn", fqdn)])

    def DeleteByID(self, id: str):
        self._Delete("id", id)

    def DeleteByShortName(self, shortName: str, fqdn: str = '*'):
        if fqdn == '*':
            self._DeleteByMultipleAND([("shortname", shortName)])
        else:
            self._DeleteByMultipleAND([("fqdn", fqdn), ("shortname", shortName)])

    def DeleteByFQDN(self, fqdn: str):
        self._Delete("fqdn", fqdn)
