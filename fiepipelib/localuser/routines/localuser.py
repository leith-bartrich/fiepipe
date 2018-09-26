import os.path

from fiepipelib.localplatform.routines.localplatform import AbstractLocalPlatformBaseRoutines


class LocalUserRoutines(object):
    """represents the local user.  Often required by various managers."""

    _local_platform: AbstractLocalPlatformBaseRoutines = None

    def get_platform(self) -> AbstractLocalPlatformBaseRoutines:
        return self._local_platform

    def __init__(self, platform: AbstractLocalPlatformBaseRoutines):
        self._local_platform = platform

    def get_home_dir(self) -> str:
        """Gets the user's home directory.  Similar to '~'"""
        ret = os.path.expanduser("~")
        if not os.path.exists(ret):
            raise RuntimeError("The home directory does not exist.")
        return ret

    def get_pipe_configuration_dir(self) -> str:
        """Gets the configuration directory for this fiepipe system for this user.  Similar to '~/.fiepipe'"""
        ret = os.path.join(self.get_home_dir(), '.fiepipe')
        if not os.path.exists(ret):
            os.makedirs(ret)
        return ret
