from fiepipelib.automanager.data.localconfig import GitLabServerMode
from fiepipelib.components.data.components import AbstractComponent


class ContainerAutomanagerConfigurationComponent(AbstractComponent):
    _active: bool = None

    def get_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        self._active = active

    _gitlab_server_mode: GitLabServerMode = None

    def get_gitlab_server_mode(self) -> GitLabServerMode:
        return self._gitlab_server_mode

    def set_gitlab_server_mode(self, gitlab_server_mode: GitLabServerMode):
        self._gitlab_server_mode = gitlab_server_mode

    _gitlab_server: str = None

    def get_gitlab_server(self) -> str:
        return self._gitlab_server

    def set_gitlab_server(self, gitlab_server: str):
        self._gitlab_server = gitlab_server

    def GetComponentName(self):
        return "automanager_configuration"

    def DeserializeJSONData(self, data: dict):
        self.set_active(data['active'])
        self.set_gitlab_server_mode(GitLabServerMode(data['gitlab_server_mode']))
        self.set_gitlab_server(data['gitlab_server'])

    def SerializeJSONData(self) -> dict:
        ret = {}
        ret['active'] = self.get_active()
        ret['gitlab_server_mode'] = self.get_gitlab_server_mode().value
        ret['gitlab_server'] = self.get_gitlab_server()
        return ret
