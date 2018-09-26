from fiepipelib.gitlabserver.shell.gitlab_hostname_input_ui import GitLabHostnameInputShellUI
from fieuishell.Shell import VarCommand


class GitLabServerNameVar(VarCommand[str]):

    def __init__(self):
        super().__init__(GitLabHostnameInputShellUI(self), "")

    def is_valid(self):
        return self.get_value() != ""
