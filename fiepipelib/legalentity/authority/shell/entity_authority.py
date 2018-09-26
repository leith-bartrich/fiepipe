import typing

import fiepipelib.legalentity.authority.data.entity_authority
import fiepipelib.shells.AbstractShell


class Shell(fiepipelib.shells.AbstractShell.AbstractShell):
    

    _entity = None
    
    def GetEntity(self):
        return self._entity
    
    def __init__(self, entity: fiepipelib.legalentity.authority.data.entity_authority.LegalEntityAuthority):
        self._entity = entity
        super(Shell, self).__init__()

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('legal_entity_authority_shell')
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["fiepipe", self.GetEntity().get_fqdn()])


    
        
    

