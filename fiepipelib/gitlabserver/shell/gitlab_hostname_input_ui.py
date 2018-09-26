from fiepipelib.gitlabserver.routines.ui.gitlab_hostname_input_ui import GitLabHostnameInputDefaultUI, GitLabhostnameInputUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


class GitLabHostnameInputDefaultShellUI(GitLabHostnameInputDefaultUI, InputDefaultModalShellUI):
    pass


class GitLabHostnameInputShellUI(GitLabhostnameInputUI, InputModalShellUI):
    pass
