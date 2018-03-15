import os.path

class localuser(object):
    """represents the local user.  Often required by various managers."""

    _localplatform = None

    def __init__(self,localplatform):
        self._localplatform = localplatform

    def GetHomeDir(self):
        """Gets the user's home directory.  Similar to '~'"""
        ret = os.path.expanduser("~")
        if not os.path.exists(ret):
            raise RuntimeError("The home directory does not exist.")
        return ret

    def GetPipeConfigurationDir(self):
        """Gets the configuration directory for this fiepipe system for this user.  Similar to '~/.fiepipe'"""
        ret = os.path.join(self.GetHomeDir(),'.fiepipe')
        if not os.path.exists(ret):
            os.makedirs(ret)
        return ret

    def GetPlatform(self):
        return self._localplatform