from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines, GitLabManagedTypeRoutines
from fiepipelib.legalentity.registry.routines.registered_entity import RegisteredEntityManagerRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class RegisteredEntityGitLabManagedTypeRoutines(GitLabManagedTypeRoutines[RegisteredEntityManagerRoutines]):
    _feedback_ui: AbstractFeedbackUI = None

    def get_feedback_ui(self):
        return self._feedback_ui

    _true_false_default_ui: AbstractModalTrueFalseDefaultQuestionUI = None

    def get_true_false_default_ui(self):
        return self._true_false_default_ui

    def __init__(self, feedback_ui: AbstractFeedbackUI, server_routines: GitLabServerRoutines, true_false_default_ui: AbstractModalTrueFalseDefaultQuestionUI):
        self._feedback_ui = feedback_ui
        self._true_false_default_ui = true_false_default_ui
        super().__init__(server_routines, feedback_ui=feedback_ui, true_false_default_ui=true_false_default_ui)

    def get_typename(self) -> str:
        return "registered_legal_entities"

    def get_local_manager_routines(self) -> RegisteredEntityManagerRoutines:
        return RegisteredEntityManagerRoutines(self.get_feedback_ui())
