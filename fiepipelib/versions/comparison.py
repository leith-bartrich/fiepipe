import abc
import distutils.version
import typing
import pkg_resources

managerInstance = None

def GetVersionComparisonManager():
    """Gets the version comparison manager.  Which is a singleton.
    
    When the singleton is create, it will load plugins marked for
    the entrypoint:
    
    fiepipe.plugin.versions.comparison.v1
    
    It will pass the function the instance as an argument.
    
    The instane has methods with which to customize version comparison on a per fqdn basis.
    
    If no customization is made, it will use a default version comparison stack.
    
    Currently, the stack checks a "Strict" comparison, and if that fails for any reaason
    it fails over to a "Loose" comparison.
    """
    global managerInstance
    if managerInstance == None:
        managerInstance = VersionComparisonManager()
    return managerInstance

class VersionComparisonManager(object):
    
    _comparers = {}
    
    def __init__(self):
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.versions.comparison.v1")
        for entrypoint in entrypoints:
            print(self.colorize("Loading versions comparison plugin: " + entrypoint.name,'green'))
            method = entrypoint.load()
            method(self)
    
    def GetDefaultCompareStack(self):
        ret = []
        ret.append(StrictVersionComparer())
        ret.append(LooseVersionComparer())
        return ret
    
    def SetCompareStack(self, stack:typing.List['VersionComparer'], fqdn:str):
        self._comparers[fqdn] = stack
    
    def Compare(self, first:str, second:str, fqdn:str):
        """Return -1 if first is less than second.
        Return 0 if they are the same
        Return 1 if first is greater than second"""
        stack = None
        if fqdn in self._comparers:
            stack = self._comparers[fqdn].copy()
        else:
            stack = self.GetDefaultCompareStack()
        stack.reverse()
        for comp in stack:
            assert isinstance(comp, VersionComparer)
            try:
                return comp.Compare(first, second)
            except:
                pass
    
    def IsSame(self, first:str, second:str, fqdn:str):
        return self.Compare(first,second,fqdn) == 0
        
    
    def IsGreater(self, first:str, second:str, fqdn:str):
        return self.Compare(first,second,fqdn) == 1
    
    def IsLess(self, first:str,second:str,fqdn:str):
        return self.Compare(first,second,fqdn) == -1
    
    
class VersionComparer(object):
    
    def __init__(self):
        pass

    def IsSame(self, first:str, second:str):
        return self.Compare(first,second) == 0
        
    
    def IsGreater(self, first:str, second:str):
        return self.Compare(first,second) == 1
    
    def IsLess(self, first:str,second:str):
        return self.Compare(first,second) == -1
    
    @abc.abstractmethod
    def Compare(self, first:str, second:str):
        """Return -1 if first is less than second.
        Return 0 if they are the same
        Return 1 if first is greater than second"""
        raise NotImplementedError()
        
class StrictVersionComparer(VersionComparer):
    
    def Compare(self, first:str, second:str):
        f = distutils.version.StrictVersion(first)
        s = distutils.version.StrictVersion(second)
        if f < s:
            return -1
        elif f > s:
            return 1
        else:
            return 0
        

class LooseVersionComparer(VersionComparer):
    
    def Compare(self, first:str, second:str):
        f = distutils.version.LooseVersion(first)
        s = distutils.version.LooseVersion(second)
        if f < s:
            return -1
        elif f > s:
            return 1
        else:
            return 0
        
