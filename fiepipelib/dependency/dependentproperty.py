class dependentproperty(object):
    """A property for an object, that allows registration for callbacks for changes"""

    _value = None
    _callbacks = None
    _parent = None

    def __init__(self, value, parent, callbacks = []):
        self._value = value
        self._callbacks = callbacks
        self._parent = parent
        for c in callbacks:
            c(None,value,self)

    def GetParent(self):
        return self._parent

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        old = self._value
        self._value = value
        for c in self._callbacks:
            c(old,value,self)

    def Register(self, callback):
        self._callbacks.append(callback)

    def DeRegister(self, callback):
        self._callbacks.remove(c)
