import shlex
import fiepipelib.applauncher.abstractlauncher
from types import FunctionType

class listlauncher (fiepipelib.applauncher.abstractlauncher.abstractlauncher):
    
    _args:list = None

    def __init__(self, args: list):
        super()
        self._args = args
        
    def GetArgs(self):
        return self._args
    
class linelauncher(listlauncher):
    
    def __init__(self, line:str):
        args = shlex.split(line)
        super(args)
    
        
        
        
        

    

    

    


