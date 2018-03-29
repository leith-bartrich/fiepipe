import subprocess

class abstractlauncher(object):


    def __init__(self):
        pass
    
    def GetArgs() -> list:
        raise NotImplementedError()

    def launch(self, echo = False):
        if echo:
            print (" ".join(self.GetArgs()))
        subprocess.Popen(self.GetArgs(),creationflags=subprocess.CREATE_NEW_CONSOLE)
        




