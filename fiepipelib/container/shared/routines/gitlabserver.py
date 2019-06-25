from fiepipelib.container.shared.routines.manager import AbstractContainerManagementInteractiveRoutines, \
    AbstractContainerManagementRoutines
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabManagedTypeInteractiveRoutines, \
    GitLabManagedTypeRoutines, GitLabServerRoutines
from fieui.FeedbackUI import AbstractFeedbackUI


class GitlabManagedContainerRoutines(GitLabManagedTypeRoutines[AbstractContainerManagementInteractiveRoutines]):
    _local_manager_routines: AbstractContainerManagementInteractiveRoutines

    def __init__(self, feedback_ui: AbstractFeedbackUI,
                 local_manager_routines: AbstractContainerManagementRoutines,
                 server_routines: GitLabServerRoutines):
        super().__init__(feedback_ui, server_routines)
        self._local_manager_routines = local_manager_routines

    def get_typename(self) -> str:
        return "container"

    def get_local_manager_routines(self) -> AbstractContainerManagementInteractiveRoutines:
        return self._local_manager_routines


class GitlabManagedContainerInteractiveRoutines(GitlabManagedContainerRoutines, GitLabManagedTypeInteractiveRoutines[
    AbstractContainerManagementInteractiveRoutines]):

    def __init__(self, feedback_ui: AbstractFeedbackUI,
                 local_manager_routines: AbstractContainerManagementInteractiveRoutines,
                 server_routines: GitLabServerRoutines):
        GitlabManagedContainerRoutines.__init__(self, feedback_ui, local_manager_routines, server_routines)
        GitLabManagedTypeInteractiveRoutines.__init__(self, feedback_ui, server_routines)
