class dependentlist(object):
    """description of class"""

    _list = None
    _parent = None

    def __init__(self,parent,items=[],insertHandlers=[],removeHandlers=[],popHandlers=[],clearHandlers=[]):
        self._list = []
        self._parent = parent
        self._insertHandlers = insertHandlers
        self._removeHandlers = removeHandlers
        self._popHandlers = popHandlers
        self._clearHandlers = clearHandlers
        for i in items:
            self.append(i)


    def append(self, item):
        self.insert(len(self._list),item)

    def insert(self, index, item):
        self._list.insert(index,item)
        for h in self._insertHandlers:
            h(index,self)

    def remove(self, item):
        self._list.remove(item)
        for h in self._removeHandlers:
            h(item,self)

    def pop(self, index):
        self._list.pop(index)
        for h in self._popHandlers:
            h(index,self)

    def clear(self, item):
        self._list.clear()
        for h in self._clearHandlers:
            h(self)

    def copy(self):
        return self._list.copy()

    _insertHandlers = None
    _removeHandlers = None
    _popHandlers = None
    _clearHandlers = None

    def Register(self,handleInsert,handleRemove,handlePop,handleClear):
        """
        Never register None.  Always at least register an empty callabe.

        Appropriate function/method headers follow.

        class methods:
        Insert(self,index,deplist)
        Remove(self,item,deplist)
        Pop(self,index,deplist)
        Clear(self,deplist)

        functions:
        Insert(index,deplist)
        Remove(item,deplist)
        Pop(index,deplist)
        Clear(deplist)
        """
        self._insertHandlers.append(handleInsert)
        self._removeHandlers.append(handleRemove)
        self._popHandlers.append(handlePop)
        self._clearHandlers.append(handleClear)

    def DeRegister(self,handleInsert,handleRemove,handlePop,handleClear):
        self._insertHandlers.remove(handleInsert)
        self._removeHandlers.remove(handleRemove)
        self._popHandlers.remove(handlePop)
        self._clearHandlers.remove(handleClear)



