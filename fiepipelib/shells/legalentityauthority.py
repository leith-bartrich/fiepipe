import sys
import fiepipelib.localuser
import fiepipelib.privatekey
import fiepipelib.authoredlegalentity
import fiepipelib.storage
import os.path
import json
import fiepipelib.shells.abstract
import cmd2


class Shell(fiepipelib.shells.abstract.Shell):


    prompt = "pipe/legal_entity_authority>"

    _localUser = None

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        super().__init__()
        self._localUser = localUser

    def getPluginNameV1(self):
        return 'legal_entity_authority'

    def do_list(self,arg):
        """Lists the entites defined under authority."""
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        for e in authority.GetAll():
            assert isinstance(e, fiepipelib.authoredlegalentity.authoredlegalentity)
            print(e.GetFQDN())

    def do_delete(self,arg):
        """Deletes the named entity
        Usage: delete [entityname]
        arg entityname: The name of the entity to delete
        """
        if arg == None:
            print("No entity specified.")
            return
        if arg == "":
            print ("No entity specified.")
            return
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        authority.DeleteByFQDN(arg)
    
    def do_create(self,arg):
        """Creates a new entity
        Usage: create [fqdn]
        arg fqdn: A fully qualified domain name for the entity.
            e.g. google.com e.g. mycompany.net
            e.g. mycompany.private
            e.g. firstname.initial.lastname.private
        """
        if arg == None:
            print("No fqdn specified.")
            return
        if arg == "":
            print ("No fqdn specified.")
            return
        
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        existing = authority.GetByFQDN(arg)
        if len(existing) > 0:
            print("Entity already exists: " + arg)
            return
        keys = []
        print("generating RSA 3072 key...")
        key = fiepipelib.privatekey.legalentityprivatekey()
        fiepipelib.privatekey.GenerateRSA3072(key)
        keys.append(key)
        print("done generating key.")
        entity = fiepipelib.authoredlegalentity.CreateFromParameters(arg,keys,[])
        authority.Set([entity])


    complete_export_registered_all = cmd2.path_complete

    def do_export_registered_all(self,arg):
        """Export all authored entities as registered entities.
        Usage: register [dir]
        arg dir: an absolute path to a directory to export to
        """
        if arg == None:
            print("No dir specified.")
            return
        if arg == "":
            print ("No dir specified.")
            return
        if not os.path.isabs(arg):
            print("The given dir is not an absolute path: " + args[1])
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        entities = authority.GetAll()
        for e in entities:
            assert isinstance(e, fiepipelib.authoredlegalentity.authoredlegalentity)
            self.do_export_registered(e.GetFQDN() + " " + arg)

    def do_register_all(self, arg):
        """Register all authored entities.
        Usage: register_all"""
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = authority.GetAll()
        toRegister = []
        for e in entities:
            assert isinstance(e,fiepipelib.authoredlegalentity.authoredlegalentity)
            toRegister.append(e.CreateRegisteredLegalEntity())
        registry.Set(toRegister)

    def do_export_registered(self,arg):
        """Export a single authored entity as a registered entity.
        Usage: export_registered [fqdn] [dir]
        arg fqdn: fully qualified domain name of entity to export
        arg dir: an absolute path to a directory to export to
        """
        if arg == None:
            print("No fqdn specified.")
            return
        if arg == "":
            print ("No fqdn specified.")
            return
        
        args = arg.split(maxsplit=1)
        if len(args) == 1:
            print("Need both a fqdn and a dir.")
            return
        if not os.path.isabs(args[1]):
            print("The given dir is not an absolute path: " + args[1])
            return
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = authority.GetByFQDN(args[0])
        for e in entities:
            entity = e.CreateRegisteredLegalEntity()
            fname = os.path.join(args[1], "registration.fiepipe." +  e.GetFQDN() + ".json")
            f = open(fname,'w')
            json.dump(fiepipelib.registeredlegalentity.ToJSONData(entity),f,indent=4)
            f.flush()
            f.close()
            print("exported to: " + fname)
            return
        print ("authored entity not found: " + arg)

    def do_register(self, arg):
        """Register a single authored entity.
        Usage: register [fqdn]
        arg fqdn: fully qualified domain name of entity to register
        """
        if arg == None:
            print("No fqdn specified.")
            return
        if arg == "":
            print ("No fqdn specified.")
            return
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = authority.GetByFQDN(arg)
        for e in entities:
            le = e.CreateRegisteredLegalEntity()
            registry.Set([le])
            return
        print ("authored entity not found: " + arg)

    def do_sign_networked_site_key(self, arg):
        """Signs the given public key with this entity's private keys.
        Usage: sign_networked_site_key [fqdn] [path]
        arg fqdn: the fully qualified domain name of the legal entity to do the signing.
        arg path: the full path to .json file with the public key to be signed.
        """
        if arg == None:
            print("No fqdn specified.")
            return
        if arg == "":
            print("No fqdn specified.")
            return
        args = arg.split(1)
        if len(args != 2):
            print("No path specified.")
        if not os.path.isabs(args[1]):
            print("Path is not an absolute path: " + args[1])
            return
        filename = os.path.basename(args[1])
        fname, ext = os.path.splitext(filename)
        if (ext != ".json"):
            print("Path isn't to a .json file: " + args[1])
            return
        f = open(args[1])
        data = json.load(f)
        f.close()
        key = fiepipelib.publickey.networkedsitepublickey()
        fiepipelib.publickey.FromJSONData(data,key)
        authority = fiepipelib.authoredlegalentity.localauthority(self._localUser)
        entities = authority.GetByFQDN(args[0])
        if len(entities) == 0:
            print("No such entity: " + args[0])
            return
        entity = entities[0]
        entity.SignPublicKey(key)
        data = fiepipelib.publickey.ToJSONData(key)
        f = open(args[1],'w')
        json.dump(data,f,indent=4)
        f.flush()
        f.close()



