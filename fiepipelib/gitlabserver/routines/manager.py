import typing

from fiepipelib.gitlabserver.data.gitlab_server import GitLabServer, GitLabServerManager
from fiepipelib.gitlabserver.routines.ui.gitlab_hostname_input_ui import GitLabHostnameInputDefaultUI
from fiepipelib.gitlabserver.routines.ui.gitlab_username_input_ui import GitLabUsernameInputDefaultUI
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fieui.FeedbackUI import AbstractFeedbackUI


class GitLabServerManagerInteractiveRoutines(AbstractLocalManagedInteractiveRoutines[GitLabServer]):
    """"Manages user's gitlab servers."""

    _hostname_input_default_ui: GitLabHostnameInputDefaultUI = None
    _username_input_default_ui: GitLabUsernameInputDefaultUI = None

    def get_hostname_input_default_ui(self):
        return self._hostname_input_default_ui

    def get_username_input_default_ui(self):
        return self._username_input_default_ui

    def __init__(self, feedback_ui: AbstractFeedbackUI, hostname_input_default_ui: GitLabHostnameInputDefaultUI,
                 username_input_default_ui: GitLabUsernameInputDefaultUI):
        self._hostname_input_default_ui = hostname_input_default_ui
        self._username_input_default_ui = username_input_default_ui
        super().__init__(feedback_ui)

    def GetManager(self) -> GitLabServerManager:
        return GitLabServerManager(LocalUserRoutines(get_local_platform_routines()))

    def GetAllItems(self) -> typing.List[GitLabServer]:
        return self.GetManager().GetAll()

    def ItemToName(self, item: GitLabServer) -> str:
        return item.get_name()

    def GetItemByName(self, name: str) -> GitLabServer:
        return self.GetManager().get_by_name(name)[0]

    async def DeleteRoutine(self, name: str):
        self.GetManager().delete_by_name(name)

    async def CreateUpdateRoutine(self, name: str):
        try:
            item = self.GetItemByName(name)
        except LookupError:
            item = self.GetManager().from_parameters(name, "hostname", "username")
        hostname = await self.get_hostname_input_default_ui().execute("GitLab hostname", item.get_hostname())
        username = await self.get_username_input_default_ui().execute("GitLab username", item.get_username())
        new_server = self.GetManager().from_parameters(name, hostname, username)
        self.GetManager().Set([new_server])
        return
