import abc
import distutils.version
import typing
import pkg_resources

managerInstance = None

def GetVersionDefaultManager():
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
        managerInstance = VersionDefaultManager()
    return managerInstance

class VersionDefaultManager(object):
    
    _defaults = {}
    
    def __init__(self):
        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.versions.default.v1")
        for entrypoint in entrypoints:
            print(self.colorize("Loading versions default plugin: " + entrypoint.name,'green'))
            method = entrypoint.load()
            method(self)
    
    
    def SetDefault(self, version:str, fqdn:str):
        self._defaults[fqdn] = version
    
    def GetDefault(self, fqdn:str):
        if fqdn in self._defaults:
            return self._defaults[fqdn]
        else:
            return "v01"
    
    
    
