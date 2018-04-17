import fiepipelib.localuser
import fiepipelib.registeredlegalentity
import fiepipelib.abstractsite
import fiepipelib.shells
import fiepipelib.shells.container
import abc

class Shell(fiepipelib.shells.abstract.Shell):
    """A shell for working in an abstract site."""

    _localUser = None
    _entity = None

    def __init__(self, localUser, entity):
        assert isinstance(localUser,fiepipelib.localuser.localuser)
        assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
        self._localUser = localUser
        self._entity = entity
        site = self.GetSite()
        assert isinstance(site, fiepipelib.abstractsite.abstractsite)
        siteName = site.GetName()
        super().__init__()

    def GetBreadCrumbsText(self):
        return self.breadcrumbs_separator.join(['pipe',self._entity.GetFQDN(),self.GetSite().GetName()])

    @abc.abstractmethod
    def GetSite(self) -> fiepipelib.abstractsite.abstractsite:
        raise NotImplementedError()

    def postloop(self):
        self.shutdownSite()
        return super().postloop()

    @abc.abstractmethod
    def shutdownSite(self):
        raise NotImplementedError()









