import functools
import typing

import cmd2
import fiepipelib.legalentity
import fiepipelib.localuser
import fiepipelib.shells
from fiepipelib.legalentity.authority.routines.entity_authority import LegalEntityAuthorityManagerInteractiveRoutines
from fiepipelib.legalentity.authority.shell.entity_authority import Shell
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines
from fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand import LocalManagedTypeCommand, T
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.legalentity.authority.routines.entity_authority import LegalEntityAuthorityManagerInteractiveRoutines

class Command(LocalManagedTypeCommand):

    def get_routines(self) -> LegalEntityAuthorityManagerInteractiveRoutines:
        return LegalEntityAuthorityManagerInteractiveRoutines(self.get_feedback_ui())

    def get_shell(self, item) -> AbstractShell:
        return Shell(item)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('legal_entity_authority_command')
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["fiepipe","legal_entity_authority_command"])

    def __init__(self, localUser: fiepipelib.localuser.routines.localuser.LocalUserRoutines):
        super(LocalManagedTypeCommand, self).__init__()




    complete_export_registered_all = functools.partial(cmd2.Cmd.path_complete, dir_only=True)

    def do_export_registered_all(self,args):
        """Export all authored entities as registered entities.
        Usage: register [dir]
        arg dir: an absolute path to a directory to export to
        """
        args = self.parse_arguments(args)

        if len(args == 0):
            self.get_feedback_ui().error("No dir specified.")
            return

        self.do_coroutine(self.GetRoutines().ExportRegisteredAllRoutine(args[0]))

    def do_register_all(self, args):
        """Register all authored entities.
        Usage: register_all"""

        self.do_coroutine(self.get_routines().RegisterAllRoutine())

    def complete_export_registered(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx,
                                        {1:self.type_complete,2:functools.partial(self.path_complete, dir_only=True)})

    #todo: move to shell?
    def do_export_registered(self,args):
        """Export a single authored entity as a registered entity.
        Usage: export_registered [fqdn] [dir]
        arg fqdn: fully qualified domain name of entity to export
        arg dir: an absolute path to a directory to export to
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.perror("No fqdn specified.")
            return

        if len(args) == 1:
            self.perror("Need both a fqdn and a dir.")
            return

        self.do_coroutine(self.get_routines().ExportRegisteredRoutine(args[0], args[1]))

    complete_register = LocalManagedTypeCommand.type_complete

    #todo: move to shell?
    def do_register(self, args):
        """Register a single authored entity.
        Usage: register [fqdn]
        arg fqdn: fully qualified domain name of entity to register
        """

        args = self.parse_arguments(args)

        if len(args) == 0:
            self.get_feedback_ui().error("No fqdn specified.")
            return

        self.do_coroutine(self.get_routines().RegisterRoutine(args[0]))

    def complete_sign_networked_site_key(self, text, line, begidx, endidx):
        return self.index_based_complete(text, line, begidx, endidx, {1:self.type_complete,2:self.path_complete})


    #TODO: move to shell?
    def do_sign_networked_site_key(self, args):
        """Signs the given public key with this entity's private keys.
        Usage: sign_networked_site_key [fqdn] [path]
        arg fqdn: the fully qualified domain name of the legal entity to do the signing.
        arg path: the full path to .json file with the public key to be signed.
        """
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.get_feedback_ui().error("No fqdn specified.")
            return

        if len(args) == 1:
            self.get_feedback_ui().error("No path specified.")
            return

        self.do_coroutine(self.GetRoutines().SignNetworkedSiteKey(args[0], args[1]))