import typing

from fiepipelib.locallymanagedtypes.data.abstractmanager import AbstractUserLocalTypeManager


class GitLabServer(object):
    """
    A GitLab Server to use for high level trust/storage and data.

    In theory, if the URL you use is a trustable URL, this is a trusworthy source.  e.g. HTTPS or SSH

    In theory, any git lab server is trustworthy if you trust your network

    As in all things, the user can use this in an insecure manner and ruin security :(
    """

    _name: str = None
    _hostname: str = None
    _username: str = None

    def get_hostname(self) -> str:
        """Full GIT url for the gitlab server"""
        return self._hostname

    def get_name(self) -> str:
        """Friendly local name for the server"""
        return self._name

    def get_username(self) -> str:
        return self._username

    def get_ssh_url(self, group: str, name: str):
        if not name.endswith(".git"):
            name = name + ".git"
        return "git@" + self.get_hostname() + ":" + group + "/" + name

    def get_https_url(self, group: str, name: str):
        if not name.endswith(".git"):
            name = name + ".git"
        return "https://" + self.get_hostname() + "/" + group + "/" + name


class GitLabServerManager(AbstractUserLocalTypeManager[GitLabServer]):
    def GetManagedTypeName(self) -> str:
        return "gitlab_server"

    def GetColumns(self) -> typing.List[typing.Tuple[str, str]]:
        ret = super().GetColumns()
        ret.append(('hostname', 'text'))
        ret.append(('name', 'text'))
        return ret

    def GetPrimaryKeyColumns(self) -> typing.List[str]:
        return ['name']
        pass

    def ToJSONData(self, item: GitLabServer) -> dict:
        ret = {}
        ret['name'] = item.get_name()
        ret['hostname'] = item.get_hostname()
        ret['username'] = item.get_username()
        return ret

    def FromJSONData(self, data: dict) -> GitLabServer:
        ret = GitLabServer()
        ret._name = data['name']
        ret._hostname = data['hostname']
        ret._username = data['username']
        return ret

    def from_parameters(self, name: str, hostname: str, username: str) -> GitLabServer:
        ret = GitLabServer()
        ret._name = name
        ret._hostname = hostname
        ret._username = username
        return ret

    def get_by_name(self, name: str):
        return super()._Get([('name', name)])

    def delete_by_name(self, name: str):
        super()._Delete("name", name)
