import typing

import fiepipelib.localuser.routines.localuser
import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.sites.data.abstractsite
import fiepipelib.shells
import fiepipelib.container.shells.container
import abc
from fiepipelib.shells.AbstractShell import AbstractShell

class Shell(AbstractShell):
    """A shell for working in an abstract site."""

    _localUser = None
    _entity = None

    def __init__(self, localUser, entity):
        assert isinstance(localUser, fiepipelib.localuser.routines.localuser.LocalUserRoutines)
        assert isinstance(entity, fiepipelib.legalentity.registry.data.registered_entity.RegisteredEntity)
        self._localUser = localUser
        self._entity = entity
        site = self.GetSite()
        assert isinstance(site, fiepipelib.sites.data.abstractsite.abstractsite)
        siteName = site.GetName()
        super().__init__()

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(Shell, self).get_plugin_names_v1()
        ret.append("site")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(['fiepipe', self._entity.get_fqdn(), self.GetSite().GetName()])


    @abc.abstractmethod
    def GetSite(self) -> fiepipelib.sites.data.abstractsite.abstractsite:
        raise NotImplementedError()

    def postloop(self):
        self.shutdownSite()
        return super().postloop()

    @abc.abstractmethod
    def shutdownSite(self):
        raise NotImplementedError()









