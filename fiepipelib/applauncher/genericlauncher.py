import os
import shlex
import typing

import fiepipelib.applauncher.abstractlauncher


class listlauncher(fiepipelib.applauncher.abstractlauncher.abstractlauncher):
    _args: list = None
    _extra_env: typing.Dict[str, str] = None

    def __init__(self, args: list, extra_env: typing.Dict[str, str] = {}):
        super(listlauncher, self).__init__()
        self._args = args
        self._extra_env = extra_env

    def GetArgs(self):
        return self._args

    def GetEnv(self) -> typing.Dict[str, str]:
        ret = os.environ.copy()
        for k, v in self._extra_env.items():
            if k in ret.keys():
                ret[k] = os.pathsep.join([ret[k], v])
            else:
                ret[k] = v
        return ret


class linelauncher(listlauncher):

    def __init__(self, line: str, extra_env: typing.Dict[str, str] = {}):
        args = shlex.split(line)
        super(linelauncher, self).__init__(args, extra_env)
