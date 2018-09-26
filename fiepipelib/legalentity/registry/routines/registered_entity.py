import typing

import fiepipelib.fiepipeserver.client
import fiepipelib.localplatform.routines.localplatform
import fiepipelib.localuser.routines.localuser
from fiepipelib.legalentity.registry.data.registered_entity import localregistry, RegisteredEntity
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedRoutines


class RegisteredEntityManagerRoutines(AbstractLocalManagedRoutines[RegisteredEntity]):

    def GetManager(self) -> localregistry:
        plat = fiepipelib.localplatform.routines.localplatform.get_local_platform_routines()
        user = fiepipelib.localuser.routines.localuser.LocalUserRoutines(plat)
        man = localregistry(user)
        return man

    def GetAllItems(self) -> typing.List[RegisteredEntity]:
        return self.GetManager().GetAll()

    def ItemToName(self, item: RegisteredEntity) -> str:
        return item.get_fqdn()

    def GetItemByName(self, name: str) -> RegisteredEntity:
        return self.GetManager().GetByFQDN(name)[0]

    async def DeleteRoutine(self, name: str):
        self.GetManager().DeleteByFQDN(name)

    async def CreateUpdateRoutine(self, name: str):
        fb = self.get_feedback_ui()
        await fb.feedback("You cannot create a registered legal entity directly.")
        await fb.feedback("It should be imported or pulled from somewhere else.")
        return

    async def Pull(self, hostname: str, username: str):
        """Pulls the registered legal entities from the given server. Make sure you trust this server.
    
        Usage: pull [hostname] [username]
        arg hostname: The hostname of the server to connect to.
        arg username: The username to use to connect.
        """
        plat = fiepipelib.localplatform.routines.localplatform.get_local_platform_routines()
        user = fiepipelib.localuser.routines.localuser.LocalUserRoutines(plat)
        client = fiepipelib.fiepipeserver.client.client(hostname, username, user)
        connection = client.getConnection()
        entities = client.get_all_regestered_legal_entities(connection)
        client.returnConnection(connection)
        client.close()

        man = self.GetManager()
        # TODO: cut down on commits by verifying them all, and then setting them all at once.
        for entity in entities:
            assert isinstance(entity, RegisteredEntity)
            await self.get_feedback_ui().feedback("Registering: " + entity.get_fqdn())
            man.Set([entity])
