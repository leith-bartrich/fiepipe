import typing

from fiepipelib.components.data.components import AbstractComponent


class ContainerAutomanagerConfigurationComponent(AbstractComponent):
    _active: bool = None

    def get_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        self._active = active

    _gitlab_server: str = None

    def get_gitlab_server(self) -> str:
        return self._gitlab_server

    def set_gitlab_server(self, gitlab_server: str):
        self._gitlab_server = gitlab_server

    _root_gitlab_server_overrides:typing.Dict[str,str] = None

    def get_root_gitlab_server_overrides(self) -> typing.Dict[str,str]:
        return self._root_gitlab_server_overrides

    _asset_gitlab_server_overrides:typing.Dict[str,str] = None

    def get_asset_gitlab_server_overrides(self) -> typing.Dict[str,str]:
        return self._asset_gitlab_server_overrides

    def __init__(self, cont):
        self._active = False
        self._root_gitlab_server_overrides = {}
        self._asset_gitlab_server_overrides = {}
        self._gitlab_server = "gitlab"
        super().__init__(cont)

    def get_root_gitlab_server(self, root_id:str):
        if root_id in self._root_gitlab_server_overrides.keys():
            return self._root_gitlab_server_overrides[root_id]
        else:
            return self.get_gitlab_server()

    def get_asset_gitlab_server(self, asset_id:str):
        if asset_id in self._asset_gitlab_server_overrides.keys():
            return self._asset_gitlab_server_overrides[asset_id]
        else:
            return self.get_gitlab_server()

    def GetComponentName(self):
        return "automanager_configuration"

    _ROOT_GITLAB_SERVER_OVERRIDES_KEY = "root_gitlab_server_overrides"
    _ASSET_GITLAB_SERVER_OVERRIDES_KEY = "asset_gitlab_server_overrides"

    def DeserializeJSONData(self, data: dict):
        self.set_active(data['active'])
        self.set_gitlab_server(data['gitlab_server'])

        if self._ROOT_GITLAB_SERVER_OVERRIDES_KEY in data:
            self._root_gitlab_server_overrides = data[self._ROOT_GITLAB_SERVER_OVERRIDES_KEY]
        else:
            self._root_gitlab_server_overrides = {}
        if self._ASSET_GITLAB_SERVER_OVERRIDES_KEY in data:
            self._asset_gitlab_server_overrides = data[self._ASSET_GITLAB_SERVER_OVERRIDES_KEY]
        else:
            self._asset_gitlab_server_overrides = {}

    def SerializeJSONData(self) -> dict:
        ret = {}
        ret['active'] = self.get_active()
        ret['gitlab_server'] = self.get_gitlab_server()
        ret[self._ROOT_GITLAB_SERVER_OVERRIDES_KEY] = self._root_gitlab_server_overrides
        ret[self._ASSET_GITLAB_SERVER_OVERRIDES_KEY] = self._asset_gitlab_server_overrides
        return ret
