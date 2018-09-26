from fiepipelib.container.shared.routines.manager import AbstractContainerManagementRoutines
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabManagedTypeRoutines, GitLabServerRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class GitlabManagedContainerRoutines(GitLabManagedTypeRoutines[AbstractContainerManagementRoutines]):

    _local_manager_routines : AbstractContainerManagementRoutines

    def __init__(self, server_routines: GitLabServerRoutines, local_manager_routines:AbstractContainerManagementRoutines, feedback_ui:AbstractFeedbackUI, true_false_default_ui:AbstractModalTrueFalseDefaultQuestionUI):
        super().__init__(server_routines,true_false_default_ui,feedback_ui)
        self._local_manager_routines = local_manager_routines

    def get_typename(self) -> str:
        return "container"

    def get_local_manager_routines(self) -> AbstractContainerManagementRoutines:
        return self._local_manager_routines


