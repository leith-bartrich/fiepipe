import typing

import fiepipelib.encryption.public.privatekey
import fiepipelib.legalentity.authority.data.entity_authority
import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.legalentity.registry.routines.registered_entity
import fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand
import fiepipelib.localuser.routines.localuser
import fiepipelib.storage
from fiepipelib.legalentity.registry.routines.registered_entity import RegisteredEntityManagerRoutines
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.legalentity.registry.shell.legal_entity import LegalEntityShell
from fiepipelib.legalentity.registry.data.registered_entity import RegisteredEntity
class RegisteredEntitiesManagerCommand(
    fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand.LocalManagedTypeCommand):

    def get_routines(self) -> RegisteredEntityManagerRoutines:
        return RegisteredEntityManagerRoutines(self.get_feedback_ui())

    def get_shell(self, item: RegisteredEntity) -> AbstractShell:
        ret = LegalEntityShell(item.get_fqdn(),self.get_user())
        return ret

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('legal_entities_command')
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["fiepipe","legal_entities_command"])

    def __init__(self):
        super().__init__()
    

    

    

    # complete_import = functools.partial(cmd2.Cmd.path_complete)
    #
    # def do_import(self,arg):
    #     """Import a legal entity from a file
    #     Usage: import [filename]
    #     arg filename:  The absolute path to a .json file which contains registeredlegalentity JSON data."""
    #     if arg is None:
    #         print("filename not specified.")
    #     if arg == "":
    #         print("filename not specified.")
    #
    #     self.do_coroutine(self.GetRoutines().ImportRoutine(arg))
    #
    # complete_import_all = functools.partial(cmd2.Cmd.path_complete,dir_only=True)
    #
    # def do_import_all(self, arg):
    #     """Import all legal entities from a directory
    #     Usage: import [pathname]
    #     arg pathname:  The absolute path to a directory which contains .json files which contain registeredlegalentity JSON data."""
    #     if arg == None:
    #         print("pathname not specified.")
    #     if arg == "":
    #         print("pathname not specified.")
    #
    #     self.do_coroutine(self.GetRoutines().ImportAllRoutine(arg))
    #
    # def complete_pull(self, text, line, begidx, endidx):
    #     return self.index_based_complete(text, line, begidx, endidx, {})
    #
    # def do_pull(self, arg):
    #     """Pulls the registered legal entities from the given server. Make sure you trust this server.
    #
    #     Usage: pull [hostname] [username]
    #     arg hostname: The hostname of the server to connect to.
    #     arg username: The username to use to connect.
    #     """
    #     if arg == None:
    #         print("No hostname given.")
    #         return
    #     if arg == "":
    #         print("No hostname given.")
    #         return
    #     args = arg.split(1)
    #     if len(args) != 2:
    #         print ("No username given")
    #         return
    #
    #     self.do_coroutine(self.GetRoutines().Pull(arg[0], args[1]))
