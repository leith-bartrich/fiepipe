import sys
import typing

from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitlabserver.shell.server_name_var_command import GitLabServerNameVar
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.shells.variables.fqdn_var_command import FQDNVarCommand


class GitLabServerShell(AbstractShell):
    _server_name_var: GitLabServerNameVar = None
    _fqdn_var: FQDNVarCommand = None

    def get_server_name(self) -> str:
        return self._server_name_var.get_value()

    def get_fqdn_var(self) -> FQDNVarCommand:
        return self._fqdn_var

    def __init__(self, server_name_var: GitLabServerNameVar, fqdn_var: FQDNVarCommand):
        self._server_name_var = server_name_var
        self._fqdn_var = fqdn_var
        self.add_variable_command(fqdn_var, "fqdn", [], True)
        self.add_variable_command(server_name_var, "server", [], False)
        super(GitLabServerShell, self).__init__()

    def get_server_routines(self):
        return GitLabServerRoutines(self.get_server_name())

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(GitLabServerShell, self).get_plugin_names_v1()
        ret.append("gitlabserver.shell")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["GitLabServer", self.get_server_name()])

    def get_fork_args(self) -> typing.List[str]:
        return [self.get_server_name()]


def main():
    server_var = GitLabServerNameVar()
    fqdn_var = FQDNVarCommand()

    if not server_var.set_from_args("server", sys.argv[1:], ""):
        print("no server specified. 'e.g. -server [name]'")
        exit(-1)

    fqdn_var.set_from_args("fqdn", sys.argv[1:], "*")

    shell = GitLabServerShell(fqdn_var=fqdn_var, server_name_var=server_var)
    shell.cmdloop()


if __file__ == "__main__":
    main()
