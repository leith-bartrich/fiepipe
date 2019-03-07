from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines, GitLabManagedTypeInteractiveRoutines
from fiepipelib.legalentity.registry.routines.registered_entity import RegisteredEntityManagerInteractiveRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class RegisteredEntityGitLabManagedTypeInteractiveRoutines(GitLabManagedTypeInteractiveRoutines[RegisteredEntityManagerInteractiveRoutines]):
    _feedback_ui: AbstractFeedbackUI = None

    def get_feedback_ui(self):
        return self._feedback_ui

    _true_false_default_ui: AbstractModalTrueFalseDefaultQuestionUI = None

    def get_true_false_default_ui(self):
        return self._true_false_default_ui

    def __init__(self, feedback_ui: GitLabServerRoutines, server_routines: AbstractFeedbackUI):
        self._feedback_ui = feedback_ui
        self._true_false_default_ui = true_false_default_ui
        super().__init__(feedback_ui=feedback_ui, server_routines=server_routines)

    def get_typename(self) -> str:
        return "registered_legal_entities"

    def get_local_manager_routines(self) -> RegisteredEntityManagerInteractiveRoutines:
        return RegisteredEntityManagerInteractiveRoutines(self.get_feedback_ui())
