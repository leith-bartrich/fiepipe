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

class Shell(fiepipelib.shells.abstract.LocalManagedTypeCommand):

    def __init__(self, localUser):
        super().__init__(localUser)
        
    def getPluginNameV1(self):
        return 'legal_entity_registry'
    
    def GetBreadCrumbsText(self):
        return "legal_entity_registry"
    
    def GetManager(self):
        return fiepipelib.registeredlegalentity.localregistry(self._localUser)
        
    def ItemToName(self, item):
        assert isinstance(item, fiepipelib.registeredlegalentity.registeredlegalentity)
        return item.GetFQDN()
        
    def GetAllItems(self):
        return self.GetManager().GetAll()

    def DeleteItem(self, name:str):
        man = self.GetManager()
        man.DeleteByFQDN(name)
        
    def GetItemByName(self, name):
        man = self.GetManager()
        return man.GetByFQDN(name)[0]
    
    def GetShell(self, item):
        assert isinstance(item, fiepipelib.registeredlegalentity.registeredlegalentity)
        ret = fiepipelib.shells.legalentity.Shell(item.GetFQDN(), self._localUser)
        return ret

    complete_import = functools.partial(cmd2.Cmd.path_complete)

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
        registry = self.GetManager()
        f = open(arg)
        data = json.load(f)
        f.close()
        entity = fiepipelib.registeredlegalentity.FromJSONData(data)
        fqdn = entity.GetFQDN()
        print("found entity: " + fqdn)
        registry.Set([entity])
        print("registered.")

    complete_import_all = functools.partial(cmd2.Cmd.path_complete)

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

    def do_pull(self, arg):
        """Pulls the registered legal entities from the given server. Make sure you trust this server.

        Usage: pull [hostname] [username]
        arg hostname: The hostname of the server to connect to.
        arg username: The username to use to connect.
        """
        if arg == None:
            print("No hostname given.")
            return
        if arg == "":
            print("No hostname given.")
            return
        args = arg.split(1)
        if len(args) != 2:
            print ("No username given")
            return
        client = fiepipelib.fiepipeserver.client.client(args[0],args[1])
        connection = client.getConnection()
        entities = client.get_all_regestered_legal_entities(connection)
        client.returnConnection(connection)
        client.close()
        registry = fiepipelib.legalentityregistry.legalentityregistry(self._localUser)
        for entity in entities:
            assert isinstance(entity, fiepipelib.registeredlegalentity.registeredlegalentity)
            registry.Register(entity)
