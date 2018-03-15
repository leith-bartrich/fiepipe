import platform
from ctypes import windll 
import string

def GetLocalPlatform():
    """Detects the local platform
    constructs the appropriate object and returns it.
    """
    #TODO: better detect platforms and construct apprpriate classes per platform.
    if platform.system() == 'Windows':
        return localplatformwindows()
    else:
        return localplatformunix()

class localplatformbase(object):
    """description of class"""

    def __init__(self):
        pass

    def getConsoleClearCommand(self):
        raise NotImplementedError()

class localplatformwindows(localplatformbase):

    def getConsoleClearCommand(self):
        return "cls"

    def getLogicalDriveLetters(self):
        """Returns a list of drive letters for logical volumes currently available.
        """
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(letter)
            bitmask >>= 1

        return drives


class localplatformunix(localplatformbase):

    def getConsoleClearCommand(self):
        return "clear"

