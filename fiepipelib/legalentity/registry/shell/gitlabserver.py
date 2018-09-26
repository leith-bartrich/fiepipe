import typing

from fiepipelib.gitlabserver.shell.gitlabserver import GitLabServerShell
from fiepipelib.gitlabserver.shell.locally_managed_type import LocalManagedUserTypeCommand, \
    LocalManagedGroupTypeCommand, T
from fiepipelib.legalentity.registry.routines.gitlabserver import RegisteredEntityGitLabManagedTypeRoutines


class RegisteredEntitiesGitLabServerUserCommand(LocalManagedUserTypeCommand[RegisteredEntityGitLabManagedTypeRoutines]):

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(RegisteredEntitiesGitLabServerUserCommand, self).get_plugin_names_v1()
        ret.append("gitlabserver.registered_entities.user.command")
        return ret

    def get_routines(self) -> RegisteredEntityGitLabManagedTypeRoutines:
        return RegisteredEntityGitLabManagedTypeRoutines(self.get_feedback_ui(),
                                                         self.get_server_shell().get_server_routines(),
                                                         self.get_true_false_default_question_modal_ui())

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["GitLab", "user", "registered_entities"])


class RegisteredEntitiesGitLabServerGroupCommand(
    LocalManagedGroupTypeCommand[RegisteredEntityGitLabManagedTypeRoutines]):

    def groupnames_complete(self, text, line, begidx, endidx) -> typing.List[str]:
        return []

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(RegisteredEntitiesGitLabServerGroupCommand, self).get_plugin_names_v1()
        ret.append("gitlabserver.registered_entitites.group.command")
        return ret

    def get_routines(self) -> T:
        return RegisteredEntityGitLabManagedTypeRoutines(self.get_feedback_ui(),
                                                         self.get_server_routines())

    def get_prompt_text(self) -> str:
        return self.prompt_separator.join(["GitLab", "[group]", "registered_entities"])
        pass


def FIEPipeShellPlugin(shell: GitLabServerShell):
    shell.add_submenu(RegisteredEntitiesGitLabServerUserCommand(shell), "registered_entities_user", ['re_u'])
    shell.add_submenu(RegisteredEntitiesGitLabServerGroupCommand(shell), "registered_entities_group", ['re_g'])
