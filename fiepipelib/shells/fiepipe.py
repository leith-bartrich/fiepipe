import typing

import fiepipelib.fiepipeserver.client
import fiepipelib.legalentity.authority.shell.entity_authority
import fiepipelib.legalentity.authority.shell.manager
import fiepipelib.legalentity.registry.data.registered_entity
import fiepipelib.legalentity.registry.shell.legal_entity
import fiepipelib.legalentity.registry.shell.manager
import fiepipelib.shells
import fiepipelib.shells.AbstractShell
import fiepipelib.storage.shells.localstorage
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.storage.routines.localstorage import LocalStorageInteractiveRoutines
from fiepipelib.storage.shells.ui.volumes import NewVolumeNameShellInputUI
from fieuishell.ChoiceInputModalUI import ChoiceInputModalShellUI
from fiepipelib.automanager.shell.automanager import AutoManagerShell
from fiepipelib.gitlabserver.shell.manager import GitLabServerManagerShell

class Shell(fiepipelib.shells.AbstractShell.AbstractShell):

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super().get_plugin_names_v1()
        ret.append('fiepipe')
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(['fiepipe'])

    intro = 'Welcome to fiepipe.  Self documenting help command: \'help\'.'
    _localUser: LocalUserRoutines = None

    def __init__(self, localUser: LocalUserRoutines):
        self._localUser = localUser
        super().__init__()
        self.add_submenu(fiepipelib.legalentity.registry.shell.manager.RegisteredEntitiesManagerCommand(),
                         "legal_entites", ["le"])
        self.add_submenu(fiepipelib.legalentity.authority.shell.manager.Command(
            localUser), "legal_entity_authority", [])
        local_storage_routines = LocalStorageInteractiveRoutines(localUser, self.get_feedback_ui(),
                                                                 ChoiceInputModalShellUI[str](self),
                                                                 NewVolumeNameShellInputUI(self))
        self.add_submenu(fiepipelib.storage.shells.localstorage.Shell(localUser, local_storage_routines),
                         "local_storage", [])
        self.add_submenu(AutoManagerShell(),"auto_manager",[])
        self.add_submenu(GitLabServerManagerShell(),"gitlab_servers",[])

    def do_register_host(self, args):
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.get_feedback_ui().error("No hostname given.")
            return

        if len(args) == 1:
            self.get_feedback_ui().error("No username given")
            return

        # we connect and ping, auto adding the host.
        client = fiepipelib.fiepipeserver.client.client(args[0], args[1], self._localUser, True)
        connection = client.getConnection()
        client.ping(connection)
        client.returnConnection(connection)
        client.close()

    def do_remove_host(self, args):
        args = self.parse_arguments(args)

        if len(args) == 0:
            self.get_feedback_ui().error("No hostname given.")
            return

        client = fiepipelib.fiepipeserver.client.client(args[0], "nobody")
        client.RemoveKnownHost()
        client.close()

    # def do_pull_known_networked_sites(self, arg):
    # """Pulls the known networked sites for a legal entity from the given server.
    # Usage: pull_known_networked_sites [hostname] [username] [entity]
    # arg hostname: The hostname of the server to connect to.
    # arg username: The username to use to connect.
    # arg entity: The fully qualified domain name of the known legal entity.
    # """
    # if arg == None:
    # print("No hostname given.")
    # return
    # if arg == "":
    # print("No hostname given.")
    # return
    # args = arg.split(2)
    # if len(args) < 2:
    # print ("No username given.")
    # return
    # if len(args) != 3:
    # print ("No entity given.")
    # fqdn = args[2]
    # client = fiepipelib.fiepipeserver.client.client(args[0],args[1])
    # connection = client.getConnection()
    # sites = client.get_all_registered_sites(connection,fqdn)
    # client.returnConnection(connection)
    # client.close()
    # registry = fiepipelib.siteregistry.siteregistry(self._localUser)
    # for site in sites:
    # assert isinstance(site,fiepipelib.networkedsite.networkedsite)
    # registry.SetNetworkedSite(site)


def main():
    p = get_local_platform_routines
    u = LocalUserRoutines(p)
    s = Shell(u)
    s.cmdloop()


if __name__ == "__main__":
    main()
