import sys
import fiepipelib.localuser
import fiepipelib.privatekey
import fiepipelib.authoredlegalentity
import fiepipelib.storage
import os.path
import json
import fiepipelib.shells.abstract
import fiepipelib.registeredlegalentity
import cmd2
import functools

class Shell(fiepipelib.shells.abstract.Shell):

    _localUser = None

    prompt = "pipe/legal_enity_registry>"

    def __init__(self, localUser):
        assert isinstance(localUser, fiepipelib.localuser.localuser)
        super().__init__()
        self._localUser = localUser

    def getPluginNameV1(self):
        return 'legal_entity_registry'

    def do_list(self,arg):
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        entities = registry.GetAll()
        for e in entities:
            assert isinstance(e, fiepipelib.registeredlegalentity.registeredlegalentity)
            print(e.GetFQDN())


    complete_import = functools.partial(cmd2.path_complete)

    def do_import(self,arg):
        """Import a legal entity from a file
        Usage: import [filename]
        arg filename:  The absolute path to a .json file which contains registeredlegalentity JSON data."""
        if arg == None:
            print("filename not specified.")
        if arg == "":
            print("filename not specified.")
        if not os.path.isabs(arg):
            print("filename is not an absolute path: " + arg)
        if not os.path.exists(arg):
            print("file not found: " + arg)
        if not os.path.isfile(arg):
            print("the path does not lead to a file: " + arg)
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        f = open(arg)
        data = json.load(f)
        f.close()
        entity = fiepipelib.registeredlegalentity.FromJSONData(data)
        fqdn = entity.GetFQDN()
        print("found entity: " + fqdn)
        registry.Set([entity])
        print("registered.")

    complete_import_all = functools.partial(cmd2.path_complete)

    def do_import_all(self, arg):
        """Import all legal entities from a directory
        Usage: import [pathname]
        arg pathname:  The absolute path to a directory which contains .json files which contain registeredlegalentity JSON data."""
        if arg == None:
            print("pathname not specified.")
        if arg == "":
            print("pathname not specified.")
        if not os.path.isabs(arg):
            print("pathname is not an absolute path.")
        if not os.path.exists(arg):
            print("path not found: " + arg)
        if not os.path.isdir(arg):
            print("the path does not lead to a directory: " + arg)
        files = os.listdir(arg)
        for file in files:
            f, e = os.path.splitext(file)
            if (e == ".json"):
                self.do_import(os.path.join(arg,file))

    def do_delete(self, arg):
        """Delete the given entity
        Usage delete [fqdn]
        arg fqdn: The fully qualified domain name of the entity to delete"""
        if arg == None:
            print("no fqdn specified.")
        if arg == "":
            print("no fqdn specified.")
        registry = fiepipelib.registeredlegalentity.localregistry(self._localUser)
        registry.DeleteByFQDN(arg)
