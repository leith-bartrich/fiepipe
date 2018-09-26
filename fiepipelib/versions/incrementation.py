import abc
import distutils.version
import typing
import pkg_resources

managerInstance = None

class IncrementationException(Exception):
    pass

class Incrementor(object):
    
    def __init__(self):
        pass

    @abc.abstractmethod
    def Increment(self, ver:str, position:int=-1) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def Decrement(self, ver:str, position:int=-1) -> str:
        raise NotImplementedError()


def GetVersionIncrementationManager():
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
        managerInstance = VersionIncrementationManager()
    return managerInstance

class VersionIncrementationManager(object):
    
    _incrementers = {}
    
    def __init__(self):
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.versions.incrementation.v1")
        for entrypoint in entrypoints:
            print(self.colorize("Loading versions incrementation plugin: " + entrypoint.name,'green'))
            method = entrypoint.load()
            method(self)
    
    def GetDefaultIncrementStack(self):
        ret = []
        ret.append(TrailingNumberIncrementor())
        ret.append(DotDelimitedIncrementor())
        return ret
    
    def SetIncrementStack(self, stack:typing.List[Incrementor], fqdn:str):
        self._incrementers[fqdn] = stack
    
    def Increment(self, first:str, fqdn:str, position:int=-1) -> str:
        """Increments the given version string"""
        stack = None
        if fqdn in self._incrementers:
            stack = self._incrementers[fqdn].copy()
        else:
            stack = self.GetDefaultIncrementStack()
        stack.reverse()
        for inc in stack:
            assert isinstance(inc, Incrementor)
            try:
                return inc.Increment(first, position)
            except:
                pass

    def Decriment(self, first:str, fqdn:str, position:int=-1) -> str:
        """Decriments the given version string"""
        stack = None
        if fqdn in self._incrementers:
            stack = self._incrementers[fqdn].copy()
        else:
            stack = self.GetDefaultIncrementStack()
        stack.reverse()
        for inc in stack:
            assert isinstance(inc, Incrementor)
            try:
                return inc.Decrement(first,position)
            except:
                pass
    
    
    

        
        
class DotDelimitedIncrementor(Incrementor):
    
    def Increment(self, ver:str, position:int=-1):
        tokens = ver.split('.')
        numerized = []
        for t in tokens:
            n = t
            try:
                n = int(t)
            except:
                pass
            numerized.append(n)

        if isinstance(numerized[position], int):
            numerized[position] = numerized[position] + 1
        else:
            raise IncrementationException("Cannot increment a non-number")
        
        outtokens = [None] * len(tokens)
        
        for i in range(0,len(tokens)):
            if isinstance(numerized[i],int):
                outtokens[i] = str(numerized[i]).zfill(len(tokens[i]))
            else:
                outtokens[i] = numerized[i]
        return ".".join(outtokens)
    
    def Decrement(self, ver:str, position:int=-1):
        tokens = ver.split('.')
        numerized = []
        for t in tokens:
            n = t
            try:
                n = int(t)
            except:
                pass
            numerized.append(n)

        if isinstance(numerized[position], int):
            numerized[position] = numerized[position] - 1
        else:
            raise IncrementationException("Cannot increment a non-number")
        
        outtokens = [None] * len(tokens)
        
        for i in range(0,len(tokens)):
            if isinstance(numerized[i],int):
                outtokens[i] = str(numerized[i]).zfill(len(tokens[i]))
            else:
                outtokens[i] = numerized[i]
        return ".".join(outtokens)
        
        
class TrailingNumberIncrementor(Incrementor):
    """position has no meaning here."""
    
    def split(self, s):
        head = s.rstrip('0123456789')
        tail = s[len(head):]
        return head, tail
    
    def Increment(self, ver:str, position:int=-1):
        """position has no meaning here."""
        head, tail = self.split(ver)
        n = int(tail)
        n = n+1
        return head + str(n).zfill(len(tail))
    
    def Decrement(self, ver:str, position:int=-1):
        """position has no meaning here."""
        head, tail = self.split(ver)
        n = int(tail)
        n = n-1
        return head + str(n).zfill(len(tail))
    


#class LooseVersionComparer(Incrementor):
    
    #def Compare(self, first:str, second:str):
        #f = distutils.version.LooseVersion(first)
        #s = distutils.version.LooseVersion(second)
        #if f < s:
            #return -1
        #elif f > s:
            #return 1
        #else:
            #return 0
        
