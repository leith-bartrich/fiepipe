import enum
import typing

from fiepipelib.locallymanagedtypes.data.abstractmanager import AbstractUserLocalTypeManager


class LegalEntityMode(enum.Enum):
    """The mode a user/system is configured to execute automatically for a particular legal entity."""

    NONE = 0  # Take no automatic action, even if active.
    USER_WORKSTATION = 1  # A user's workstation.  Do what's convenient for the user.  Who may be doing all kinds of things.



class LegalEntityConfig(object):

    _active: bool = True

    def IsActive(self) -> bool:
        return self._active

    def set_active(self, active:bool):
        self._active = active

    _fqdn: str = None

    def get_fqdn(self) -> str:
        return self._fqdn

    _mode: LegalEntityMode = None

    def get_mode(self) -> LegalEntityMode:
        return self._mode

    def set_mode(self, mode:LegalEntityMode):
        self._mode = mode


    _gitlab_server: str = None

    def get_gitlab_server(self):
        return self._gitlab_server

    def set_gitlab_server(self, server:str):
        self._gitlab_server = server

class LegalEntityConfigManager(AbstractUserLocalTypeManager[LegalEntityConfig]):

    def GetManagedTypeName(self) -> str:
        return "automan_legal_entity_config"

    def GetColumns(self) -> typing.List[typing.Tuple[str, str]]:
        ret = super(LegalEntityConfigManager, self).GetColumns()
        ret.append(("fqdn", "text"))
        return ret

    def GetPrimaryKeyColumns(self) -> typing.List[str]:
        return ["fqdn"]

    def ToJSONData(self, item: LegalEntityConfig) -> dict:
        ret = {}
        ret["fqdn"] = item.get_fqdn()
        ret["active"] = item.IsActive()
        ret["mode"] = item.get_mode().value
        ret["gitlab_server"] = item.get_gitlab_server()
        return ret

    def FromJSONData(self, data: dict) -> LegalEntityConfig:
        ret = LegalEntityConfig()
        ret._active = data['active']
        ret._mode = LegalEntityMode(data['mode'])
        ret._fqdn = data['fqdn']
        ret._gitlab_server = data['gitlab_server']
        return ret

    def FromParameters(self, fqdn: str, active: bool, mode: LegalEntityMode, gitlab_server:str) -> LegalEntityConfig:
        ret = LegalEntityConfig()
        ret._fqdn = fqdn
        ret._active = active
        ret._mode = mode
        ret._gitlab_server = gitlab_server
        return ret

    def get_by_fqdn(self, fqdn:str) -> typing.List[LegalEntityConfig]:
        return self._Get([("fqdn",fqdn)])

    def delete_by_fqdn(self, fqdn:str):
        self._Delete("fqdn",fqdn)


