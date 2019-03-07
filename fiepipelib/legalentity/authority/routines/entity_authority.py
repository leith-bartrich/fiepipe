import json
import os
import typing

import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.localplatform.routines.localplatform
import fiepipelib.localuser.routines.localuser
import fiepipelib.encryption.public.privatekey
import fiepipelib.encryption.public.publickey
from fiepipelib.legalentity.authority.data.entity_authority import LegalEntityAuthority, \
    CreateFromParameters
from fiepipelib.legalentity.authority.data.entity_authority_manager import LegalEntityAuthorityManager
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines


class LegalEntityAuthorityManagerInteractiveRoutines(AbstractLocalManagedInteractiveRoutines[LegalEntityAuthority]):

    def GetManager(self) -> LegalEntityAuthorityManager:
        plat = fiepipelib.localplatform.routines.localplatform.get_local_platform_routines()
        user = fiepipelib.localuser.routines.localuser.LocalUserRoutines(plat)
        man = LegalEntityAuthorityManager(user)
        return man

    def GetAllItems(self) -> typing.List[LegalEntityAuthority]:
        return self.GetManager().GetAll()

    def ItemToName(self, item: LegalEntityAuthority) -> str:
        return item.get_fqdn()

    def GetItemByName(self, name: str) -> LegalEntityAuthority:
        return self.GetManager().GetByFQDN(name)[0]

    async def DeleteRoutine(self, name: str):
        self.GetManager().DeleteByFQDN(name)

    async def CreateUpdateRoutine(self, name: str):
        authority = self.GetManager()
        existing = authority.GetByFQDN(name)
        if len(existing) > 0:
            await self.get_feedback_ui().error("Entity already exists: " + name)
            raise IOError("Already exists.")
        keys = []
        await self.get_feedback_ui().feedback("generating RSA 3072 key...")
        key = fiepipelib.encryption.public.privatekey.legalentityprivatekey()
        fiepipelib.encryption.public.privatekey.GenerateRSA3072(key)
        keys.append(key)
        await self.get_feedback_ui().feedback("done generating key.")
        entity = CreateFromParameters(name, keys, [])
        authority.Set([entity])

    async def ExportRegisteredAllRoutine(self, path):
        """Export all authored entities as registered entities.
        arg path: an absolute path to a directory to export to
        """
        if not os.path.isabs(path):
            await self.get_feedback_ui().error("The given dir is not an absolute path: " + path)
            raise IOError("Not absolute: " + path)

        entities = self.GetAllItems()
        for e in entities:
            await self.ExportRegisteredRoutine(e.get_fqdn(), path)

    async def RegisterAllRoutine(self):
        """Register all authored entities."""
        authority = self.GetManager()
        registry = fiepipelib.legalentity.registry.data.registered_entity.localregistry(authority._localUser)
        entities = authority.GetAll()
        toRegister = []
        for e in entities:
            assert isinstance(e, LegalEntityAuthority)
            toRegister.append(e.generate_registered_legal_entity())
        registry.Set(toRegister)

    async def ExportRegisteredRoutine(self, fqdn: str, dirPath: str):
        """Export a single authored entity as a registered entity.
        arg fqdn: fully qualified domain name of entity to export
        arg dirPath: an absolute path to a directory to export to
        """
        if not os.path.isabs(dirPath):
            await self.get_feedback_ui().error("The given dir is not an absolute path: " + dirPath)
            raise IOError("Not absolute: " + dirPath)
        entities = self.GetManager().GetByFQDN(fqdn)

        if len(entities) == 0:
            await self.get_feedback_ui().error("authored entity not found: " + fqdn)
            raise IOError("Not found.")

        for e in entities:
            entity = e.generate_registered_legal_entity()
            fname = os.path.join(dirPath, "registration.fiepipe." + e.get_fqdn() + ".json")
            f = open(fname, 'w')
            json.dump(fiepipelib.legalentity.registry.data.registered_entity.ToJSONData(entity), f, indent=4)
            f.flush()
            f.close()
            await self.get_feedback_ui().feedback("exported to: " + fname)
            return

    async def RegisterRoutine(self, fqdn: str):
        """Register a single authored entity.
        arg fqdn: fully qualified domain name of entity to register
        """
        authority = self.GetManager()
        registry = fiepipelib.legalentity.registry.data.registered_entity.localregistry(authority._localUser)
        entities = authority.GetByFQDN(fqdn)

        if len(entities) == 0:
            await self.get_feedback_ui().error("authored entity not found: " + fqdn)
            raise IOError("Not found.")

        for e in entities:
            le = e.generate_registered_legal_entity()
            registry.Set([le])
            return

    async def SignNetworkedSiteKey(self, fqdn: str, path: str):
        """Signs the given public key with this entity's private keys.
        arg fqdn: the fully qualified domain name of the legal entity to do the signing.
        arg path: the full path to .json file with the public key to be signed.
        """
        if not os.path.isabs(path):
            await self.get_feedback_ui().error("Path is not an absolute path: " + path)
            raise IOError("Not absolute: " + path)
        filename = os.path.basename(path)
        fname, ext = os.path.splitext(filename)
        if (ext.lower() != ".json"):
            await self.get_feedback_ui().error("Path isn't to a .json file: " + path)
            raise IOError("Wrong filetype: " + path)
        f = open(path)
        data = json.load(f)
        f.close()
        key = fiepipelib.encryption.public.publickey.networkedsitepublickey()
        fiepipelib.encryption.public.publickey.FromJSONData(data, key)
        authority = self.GetManager()
        entities = authority.GetByFQDN(fqdn)

        if len(entities) == 0:
            await self.get_feedback_ui().error("No such entity: " + fqdn)
            raise IOError("Not found: " + fqdn)

        entity = entities[0]
        entity.sign_public_key(key)
        data = fiepipelib.encryption.public.publickey.ToJSONData(key)
        f = open(path, 'w')
        json.dump(data, f, indent=4)
        f.flush()
        f.close()
