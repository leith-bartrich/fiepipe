import abc
import typing


class AbstractComponent(object):
    """
    A base class for components that serialize to objects that contain components in a _components field.
    The _components field should contain a dictionary.  It should have string keys.  The values
    should be JSON Data (dicts from/for the json module)

    By storing components this abstract way, we can allow component data to be handled by plugins and also
    have their data preserved through a load/save cycle even without the plugins loaded.
    """

    _container = None

    def get_container(self) -> object:
        return self._container

    def __init__(self, cont):
        assert hasattr(cont, "_components")
        assert isinstance(cont._components, dict)
        self._container = cont

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

    def _RemoveComponentJSONData(self, name, raiseOnNotFound=False):
        assert isinstance(name, str)
        if raiseOnNotFound:
            self._container._components.pop(name)
        else:
            self._container._components.pop(name, d={})

    def Exists(self):
        """Returns true if this component has stored data in the container."""
        return self._HasComponentJSONData(self.GetComponentName())

    def Commit(self):
        """Writes data to container."""
        data = self.SerializeJSONData()
        self._SetComponentJSDONData(self.GetComponentName(), data)

    def Clear(self):
        """Clears data from container."""
        self._RemoveComponentJSONData(self.GetComponentName(), False)

    def Load(self):
        """Loads data from container if it exists."""
        if self.Exists():
            data = self._GetComponentJSONData(self.GetComponentName())
            self.DeserializeJSONData(data)

    @abc.abstractmethod
    def GetComponentName(self):
        """Returns the name of the component's data."""
        raise NotImplementedError()

    @abc.abstractmethod
    def DeserializeJSONData(self, data: dict):
        """Override this and call the super.  Populates this object's fields from the given JSON data."""
        pass

    @abc.abstractmethod
    def SerializeJSONData(self) -> dict:
        """Override this and call the super.  Saves this object's fields to JSON data."""
        return {}


class UnknownComponent(AbstractComponent):
    """A concrete implementation of a component that stands in for a more specific implementation when you don't have one.
    Can be used to preserve component data in an implementation the requires a reference to all components in memory.

    It just holds the serialized data in memory when deserialized and hands it back when it is re-serialized.

    You can get the data via GetSerializedData, which returs a dictionary.
    If you want to present it, you could pass it to the json module dumps method."""

    _data = None
    _name = None

    def __init__(self, cont, name: str):
        self._name = name
        self._data = {}
        super().__init__(cont)

    def GetSerializedData(self) -> dict:
        """Returns the serialized data.  For whatever reason."""
        return self._data

    def SetSerializedData(self, data: dict):
        """Sets the serialized data.  For whatever reason.  This probably isn't safe to use unless you know what you
        are doing."""
        self._data = data

    def SetComponentName(self, name: str):
        """Sets the component name. For whatever reason.  This probably isn't safe to use unless you know what you
        are doing."""
        self._name = name

    def GetComponentName(self) -> str:
        return self._name

    def DeserializeJSONData(self, data):
        self._data = data

    def SerializeJSONData(self) -> dict:
        return self._data


T = typing.TypeVar("T")


class AbstractItemListComponent(AbstractComponent, typing.Generic[T]):
    """An abstract generic component that exposes itself as a list of items of type 'T'"""

    _items: typing.List[T] = None

    def __init__(self, cont):
        self._items = []
        super().__init__(cont)

    def DeserializeJSONData(self, data: dict):
        self._items.clear()
        for itemData in data['items']:
            self._items.append(self.ItemFromJSONData(itemData))

    def SerializeJSONData(self):
        ret = []
        for i in self._items:
            ret.append(self.ItemToJSONData(i))
        return {'items': ret}

    def GetItems(self) -> typing.List[T]:
        """Gets the actual list (not a copy.)
        Modify it directly.  Then commit it."""
        return self._items

    @abc.abstractmethod
    def ItemToJSONData(self, item: T) -> dict:
        raise NotImplementedError()

    @abc.abstractmethod
    def ItemFromJSONData(self, data: dict) -> T:
        raise NotImplementedError()


NT = typing.TypeVar("NT")


class AbstractNamedItemListComponent(AbstractItemListComponent[NT], typing.Generic[NT]):

    @abc.abstractmethod
    def item_to_name(self, item: NT) -> str:
        raise NotImplementedError()

    def get_by_name(self, name: str) -> NT:
        for i in self.GetItems():
            if self.item_to_name(i) == name:
                return i
        raise LookupError("No such item: " + name)

    def delete_by_name(self, name: str):
        try:
            i = self.get_by_name(name)
            self.GetItems().remove(i)
        except LookupError:
            pass


V = typing.TypeVar("V")


class AbstractStringKeyedDictComponent(AbstractComponent, typing.Generic[V]):
    """A abstract generic component that exposes itself as a string keyed dictionary of Items of type 'V'"""

    _data: typing.Dict[str, V] = None

    def __init__(self, cont):
        self._data = {}
        super().__init__(cont)

    def DeserializeJSONData(self, data: dict):
        self._data.clear()
        for k in data.keys():
            self._data[k] = self.ItemFromJSONData(data[k])

    def SerializeJSONData(self):
        ret = {}
        for k in self._data.keys():
            ret[k] = self.ItemToJSONData(self._data[k])
        return ret

    def GetDict(self) -> typing.Dict[str, V]:
        """Gets the actual dictionary (not a copy)
        To modify it, do so directly.  Then commit the component."""
        return self._data

    @abc.abstractmethod
    def ItemToJSONData(self, item: V) -> dict:
        raise NotImplementedError()

    @abc.abstractmethod
    def ItemFromJSONData(self, data: dict) -> V:
        raise NotImplementedError()
