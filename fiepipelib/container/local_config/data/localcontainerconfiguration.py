import typing

import fiepipelib.locallymanagedtypes.data.abstractmanager
from fiepipelib.container.shared.data.container import Container


def config_from_json_data(data):
    ret = LocalContainerConfiguration()
    ret._id = data['id']
    ret._components = data['components']
    return ret


def config_to_json_data(conf):
    assert isinstance(conf, LocalContainerConfiguration)
    ret = {}
    ret['version'] = 1
    ret['id'] = conf._id
    ret['components'] = conf._components
    return ret


def config_from_parameters(id, components={}):
    assert isinstance(components, dict)
    ret = LocalContainerConfiguration()
    ret._id = id
    ret._components = components
    return ret


class LocalContainerConfiguration(object):

    _id = None

    def GetID(self):
        return self._id

    _components = None

    def __init__(self):
        self._components = {}


class LocalContainerConfigurationManager(
    fiepipelib.locallymanagedtypes.data.abstractmanager.AbstractUserLocalTypeManager[LocalContainerConfiguration]):

    def FromJSONData(self, data) -> LocalContainerConfiguration:
        return config_from_json_data(data)

    def ToJSONData(self, item: LocalContainerConfiguration) -> dict:
        return config_to_json_data(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("id", "text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["id"]

    def GetManagedTypeName(self):
        return "containerlocalconfiguration"

    def GetByID(self, uid) -> typing.List[LocalContainerConfiguration]:
        return self._Get([("id", uid)])

    def GetByContainer(self, cont: Container) -> typing.List[LocalContainerConfiguration]:
        ret = self.GetByID(cont.GetID())
        return ret

    def DeleteByID(self, uid):
        self._Delete("id", uid)

    def DeleteByContainer(self, cont: Container):
        self.DeleteByID(cont.GetID())