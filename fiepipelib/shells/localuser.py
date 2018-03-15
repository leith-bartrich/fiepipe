import sys
import fiepipelib.localuser
import os.path
import json
import fiepipelib.shells.abstract


class Shell(fiepipelib.shells.abstract.Shell):

    prompt = 'pipe/local_user>'
    _localUser = None

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        super().__init__()
        self._localUser = localUser

    def do_print_home_dir(self,arg):
        """Prints the homedir of the current local user"""
        print(self._localUser.GetHomeDir())


