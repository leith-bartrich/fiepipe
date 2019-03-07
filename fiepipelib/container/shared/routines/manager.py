import abc
import typing

import fieui.FeedbackUI
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager
from fiepipelib.container.shared.data.container import Container, LocalContainerManager, GenerateNewID, \
    ContainerFromParameters
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines, \
    AbstractLocalManagedRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI
from fieui.InputModalUI import AbstractInputModalUI


class AbstractContainerManagementRoutines(AbstractLocalManagedRoutines[Container]):

    def GetManager(self) -> LocalContainerManager:
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        return LocalContainerManager(user)

    @abc.abstractmethod
    def GetAllItems(self) -> typing.List[Container]:
        raise NotImplementedError()

    def ItemToName(self, item: Container) -> str:
        return item.GetShortName()

    @abc.abstractmethod
    def GetItemByName(self, name: str) -> Container:
        raise NotImplementedError()

    @abc.abstractmethod
    async def DeleteRoutine(self, name: str):
        """Override and call super.  Then do the deletion."""
        await self.delete_local_configuration_routine(name)

    async def delete_local_configuration_routine(self, name: str):
        """Deletes the local configuration for a container.
        arg name: The name of the container to de-configure.
        """
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)
        manager = LocalContainerConfigurationManager(user)
        cont = self.GetItemByName(name)
        manager.DeleteByID(cont.GetID())


class AbstractContainerManagementInteractiveRoutines(AbstractContainerManagementRoutines,
                                                     AbstractLocalManagedInteractiveRoutines[Container]):
    """Routines for addressing the container mangement system."""

    _desc_input_ui: AbstractInputDefaultModalUI[str] = None

    def get_desc_input_ui(self) -> fieui.InputDefaultModalUI.AbstractInputDefaultModalUI[str]:
        return self._desc_input_ui

    def __init__(self, feedback_ui: fieui.FeedbackUI.AbstractFeedbackUI,
                 desc_input_ui: fieui.InputDefaultModalUI.AbstractInputDefaultModalUI[str]):
        self._desc_input_ui = desc_input_ui
        AbstractContainerManagementRoutines.__init__(self,feedback_ui)
        AbstractLocalManagedInteractiveRoutines[Container].__init__(feedback_ui,desc_input_ui)

    @abc.abstractmethod
    async def CreateUpdateRoutine(self, name: str):
        """Create a new container and put it in the local registry."""
        raise NotImplementedError()


class FQDNContainerManagementRoutines(AbstractContainerManagementRoutines):

    _fqdn = None

    def __init__(self, feedback_ui: fieui.FeedbackUI.AbstractFeedbackUI,fqdn:str):
        self._fqdn = fqdn
        AbstractContainerManagementRoutines.__init__(self,feedback_ui)

    def get_fqdn(self) -> str:
        return self._fqdn

    async def DeleteRoutine(self, name: str):
        await super(FQDNContainerManagementRoutines, self).DeleteRoutine(name)
        man = self.GetManager()
        man.DeleteByShortName(shortName=name, fqdn='*')

    def GetAllItems(self) -> typing.List[Container]:
        man = self.GetManager()
        return man.GetByFQDN(self.get_fqdn())

    def GetItemByName(self, name: str) -> Container:
        man = self.GetManager()
        containers = man.GetByShortName(shortName=name, fqdn=self.get_fqdn())
        if len(containers) == 1:
            return containers[0]
        else:
            LookupError("Wrong number of containers found.  Looking for 1.  Got: " + str(len(containers)))


class FQDNContainerManagementInteractiveRoutines(FQDNContainerManagementRoutines,
                                                 AbstractContainerManagementInteractiveRoutines):
    """Routines for addressing the container managment system for one fqdn"""

    def __init__(self, fqdn: str, feedback_ui: fieui.FeedbackUI.AbstractFeedbackUI,
                 desc_input_ui: fieui.InputDefaultModalUI.AbstractInputDefaultModalUI[str]):
        AbstractContainerManagementInteractiveRoutines.__init__(self,feedback_ui,desc_input_ui)
        FQDNContainerManagementRoutines.__init__(self,feedback_ui,fqdn)

    async def CreateUpdateRoutine(self, name: str):
        uuid = GenerateNewID()
        man = self.GetManager()
        desc = await self.get_desc_input_ui().execute("Description", "A new container.")
        container = ContainerFromParameters(self.get_fqdn(), uuid, name, desc)
        man.Set([container])


class AllContainerManagementRoutines(AbstractContainerManagementRoutines):

    def GetAllItems(self) -> typing.List[Container]:
        man = self.GetManager()
        return man.GetAll()

    def GetItemByName(self, name: str) -> Container:
        """WARNING:  Containers from different FQDNs might share the same name!"""
        man = self.GetManager()
        containers = man.GetByShortName(shortName=name)
        if len(containers) == 1:
            return containers[0]
        else:
            raise LookupError("Wrong number of containers found.  Expecting one.  Got: " + str(len(containers)))

    async def DeleteRoutine(self, name: str):
        await super(AllContainerManagementRoutines, self).DeleteRoutine(name)
        man = self.GetManager()
        man.DeleteByShortName(shortName=name, fqdn='*')


class AllContainerManagementInteractiveRoutines(AllContainerManagementRoutines,
                                                AbstractContainerManagementInteractiveRoutines):
    """Routines for addressing the container managment of all fqdns."""

    _fqdn_input_ui: AbstractInputModalUI[str] = None

    def __init__(self, feedback_ui: fieui.FeedbackUI.AbstractFeedbackUI,
                 desc_input_ui: fieui.InputDefaultModalUI.AbstractInputDefaultModalUI[str],
                 fqdn_input_ui: AbstractInputModalUI[str]):
        self._fqdn_input_ui = fqdn_input_ui
        super().__init__(feedback_ui, desc_input_ui)

    async def CreateUpdateRoutine(self, name: str):
        newid = GenerateNewID()
        fqdn = await self._fqdn_input_ui.execute("Fully qualified domain name (FQDN)")
        desc = await self.get_desc_input_ui().execute("Description", "A new container.")
        container = ContainerFromParameters(fqdn=fqdn, id=newid, shortname=name, description=desc)
        man = self.GetManager()
        man.Set([container])
