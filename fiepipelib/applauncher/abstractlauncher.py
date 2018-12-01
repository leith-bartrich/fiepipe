import subprocess
import typing

class abstractlauncher(object):


    def __init__(self):
        pass
    
    def GetArgs(self) -> list:
        raise NotImplementedError()

    def GetEnv(self) -> typing.Dict[str,str]:
        raise NotImplementedError()

    def launch(self, echo = False):
        if echo:
            print (" ".join(self.GetArgs()))
        subprocess.Popen(self.GetArgs(),env=self.GetEnv(),creationflags=subprocess.CREATE_NEW_CONSOLE)
        




