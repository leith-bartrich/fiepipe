from fiepipelib.gitlabserver.routines.ui.gitlab_username_input_ui import GitLabUsernameInputDefaultUI, \
    GitLabUsernameInputUI
from fieuishell.ModalInputDefaultUI import InputDefaultModalShellUI
from fieuishell.ModalInputUI import InputModalShellUI


class GitLabUsernameInputDefaultShellUI(GitLabUsernameInputDefaultUI, InputDefaultModalShellUI):
    pass


class GitLabUsernameInputShellUI(GitLabUsernameInputUI, InputModalShellUI):
    pass
