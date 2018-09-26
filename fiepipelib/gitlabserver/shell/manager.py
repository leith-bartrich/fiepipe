import typing

from fiepipelib.gitlabserver.data.gitlab_server import GitLabServer
from fiepipelib.gitlabserver.routines.manager import GitLabServerManagerRoutines
from fiepipelib.gitlabserver.shell.gitlab_hostname_input_ui import GitLabHostnameInputDefaultShellUI
from fiepipelib.gitlabserver.shell.gitlab_username_input_ui import GitLabUsernameInputDefaultShellUI
from fiepipelib.gitlabserver.shell.gitlabserver import GitLabServerShell
from fiepipelib.gitlabserver.shell.server_name_var_command import GitLabServerNameVar
from fiepipelib.locallymanagedtypes.shells.AbstractLocalManagedTypeCommand import LocalManagedTypeCommand
from fiepipelib.shells.AbstractShell import AbstractShell
from fiepipelib.shells.variables.fqdn_var_command import FQDNVarCommand


class GitLabServerManagerShell(LocalManagedTypeCommand[GitLabServer]):

    def get_routines(self) -> GitLabServerManagerRoutines:
        return GitLabServerManagerRoutines(feedback_ui=self.get_feedback_ui(),
                                           hostname_input_default_ui=GitLabHostnameInputDefaultShellUI(self),
                                           username_input_default_ui=GitLabUsernameInputDefaultShellUI(self))

    def get_shell(self, item: GitLabServer) -> AbstractShell:
        # no shell currently.  We call super instead.
        server_name = GitLabServerNameVar()
        server_name.set_value(item.get_name())
        fqdn_var = FQDNVarCommand()
        return GitLabServerShell(server_name, fqdn_var)

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(GitLabServerManagerShell, self).get_plugin_names_v1()
        ret.append("gitlabserver.manager")
        return ret

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(['GitLabServer', 'Manager'])


def main():
    shell = GitLabServerManagerShell()
    shell.cmdloop()


if __name__ == '__main__':
    main()
