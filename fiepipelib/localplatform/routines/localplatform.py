import abc
import platform
import string
import typing
from ctypes import windll


def get_local_platform_routines():
    """Detects the local platform
    constructs the appropriate object and returns it.
    """
    # TODO: better detect platforms and construct apprpriate classes per platform.
    if platform.system() == 'Windows':
        return LocalPlatformWindowsRoutines()
    else:
        return LocalPlatformUnixRoutines()


class AbstractLocalPlatformBaseRoutines(object):
    """Abstract base class of all local platforms"""

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_console_clear_command(self) -> str:
        """The native command to run that will clear the console screen."""
        raise NotImplementedError()


class LocalPlatformWindowsRoutines(AbstractLocalPlatformBaseRoutines):

    def get_console_clear_command(self):
        return "cls"

    def get_logical_drive_letters(self) -> typing.List[str]:
        """Returns a list of drive letters for logical volumes currently available.
        """
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(letter)
            bitmask >>= 1

        return drives


class LocalPlatformUnixRoutines(AbstractLocalPlatformBaseRoutines):

    def get_console_clear_command(self):
        return "clear"
