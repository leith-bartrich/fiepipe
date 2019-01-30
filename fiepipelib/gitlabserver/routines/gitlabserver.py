import abc
import os
import os.path
import os.path
import pathlib
import typing

import git

from fiepipelib.git.routines.remote import create_update_remote, get_commits_behind, get_commits_ahead
from fiepipelib.git.routines.repo import RepoExists, DeleteLocalRepo
from fiepipelib.gitlabserver.data.gitlab_server import GitLabServer, GitLabServerManager
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedRoutines
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class GitLabServerRoutines(object):
    """Abstract base routines for a gitlab server manager.  Enforces some basic naming conventions
    on the gilab server.  Such as prepending "fiepipe_" to a gitlab project, and a standardized
    local location for the local repo/worktree.

    currenlty uses SSH but may change in the future."""

    _server_name: str = None

    def __init__(self, server_name: str):
        self._server_name = server_name

    def get_server_name(self) -> str:
        return self._server_name

    def get_user_routines(self) -> LocalUserRoutines:
        return LocalUserRoutines(get_local_platform_routines())

    def get_manager(self) -> GitLabServerManager:
        return GitLabServerManager(self.get_user_routines())

    def get_server(self) -> GitLabServer:
        return self.get_manager().get_by_name(self.get_server_name())[0]

    def local_path_for_type_registry(self, server_name: str, group_name: str, type_name: str) -> str:
        pipeconfigdir = self.get_user_routines().get_pipe_configuration_dir()
        ret = os.path.join(pipeconfigdir, "gitlabserver", server_name, group_name, type_name + ".git")
        pth = pathlib.Path(ret)
        if not pth.exists():
            pth.mkdir(parents=True)
        return ret

    def remote_path_for_entity_registry(self, group_name: str, type_name: str) -> str:
        server = self.get_server()
        return server.get_ssh_url(group_name, "fiepipe_" + type_name + ".git")

    def remote_path_for_gitroot(self, group_name: str, root_id: str) -> str:
        server = self.get_server()
        mangled_root_id = str(root_id)
        mangled_root_id = mangled_root_id.replace("-", "")
        mangled_root_id = mangled_root_id.replace("_", "")
        mangled_root_id = mangled_root_id.replace(" ", "")
        return server.get_ssh_url(group_name, "fiepipe_gitroot_" + mangled_root_id + ".git")

    def remote_path_for_gitasset(self, group_name: str, asset_id: str) -> str:
        server = self.get_server()
        mangled_asset_id = str(asset_id)
        mangled_asset_id = mangled_asset_id.replace("-", "")
        mangled_asset_id = mangled_asset_id.replace("_", "")
        mangled_asset_id = mangled_asset_id.replace(" ", "")
        return server.get_ssh_url(group_name, "fiepipe_gitasset_" + mangled_asset_id + ".git")

    def group_name_from_fqdn(self, fqdn: str):
        return "fiepipe." + fqdn


T = typing.TypeVar("T", bound=AbstractLocalManagedRoutines)


class GitLabGitStorageRoutines(abc.ABC):
    _server_routines: GitLabServerRoutines = None

    def get_server_routines(self) -> GitLabServerRoutines:
        return self._server_routines

    @abc.abstractmethod
    def get_group_name(self) -> str:
        raise NotImplementedError()

    def __init__(self, server_routines: GitLabServerRoutines):
        self._server_routines = server_routines

    @abc.abstractmethod
    def get_remote_url(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_repo_path(self) -> str:
        raise NotImplementedError()

    async def pull(self, feedback_ui: AbstractFeedbackUI):

        server = self.get_server_routines().get_server()
        local_repo_path = self.get_local_repo_path()
        remote_url = self.get_remote_url()

        await feedback_ui.output("Pulling: " + local_repo_path + " from: " + remote_url)

        if RepoExists(local_repo_path):
            repo = git.Repo(local_repo_path)
            remote = create_update_remote(repo, "origin", remote_url)
            remote = create_update_remote(repo, server.get_name(), remote_url)
            await feedback_ui.output(("Pulling from master: " + local_repo_path + " <- " + remote_url))
            remote.pull("master")
        else:
            await feedback_ui.error("Repository doesn't exist.  Cannot pull.  You might want to clone it or init it?")
            return

    async def push(self, feedback_ui: AbstractFeedbackUI):

        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        await feedback_ui.output("Pushing: " + local_path + " to: " + remote_url)

        if not RepoExists(local_path):
            await feedback_ui.error("No local worktree.  You might need to create or pull it first.")
            return

        repo = git.Repo(local_path)

        if repo.is_dirty(untracked_files=True):
            await feedback_ui.error("Worktree is dirty or has untracked files.  Aborting.")
            return

        # we push to the server even if there was no commit because this is a "push" command.
        # this works for submodules too, we think.  Maybe?
        remote = create_update_remote(repo, server.get_name(), remote_url)
        await feedback_ui.output("Pushing to master: " + local_path + " -> " + remote_url)
        remote.push("master")

    async def is_behind_remote(self, feedback_ui: AbstractFeedbackUI) -> bool:

        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        repo = git.Repo(local_path)
        server_name = server.get_name()

        await feedback_ui.output("Updating remote " + server_name + " to: " + remote_url)
        create_update_remote(repo, server_name, remote_url)

        commits_behind = get_commits_behind(repo, "master", server_name)

        return len(commits_behind) != 0

    async def is_aheadof_remote(self, feedback_ui: AbstractFeedbackUI) -> bool:

        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        repo = git.Repo(local_path)
        server_name = server.get_name()

        await feedback_ui.output("Updating remote " + server_name + " to: " + remote_url)
        create_update_remote(repo, server_name, remote_url)

        commits_ahead = get_commits_ahead(repo, "master", server_name)

        return len(commits_ahead) != 0


class GitLabManagedTypeRoutines(typing.Generic[T]):
    """Abstract Routines for sharing Local Managed Types through GitLab.

    The scope of the locally managed types comes from the local type manager returned from the
    'get_locally_managed_routines' method.

    e.g. if the manager is FQDN scoped, then pushes will automatically by FQDN scoped
    because a call to "getall" in the manager will automatically enforce the scope.  Similarly, a
    find by name will also be scoped by the manager.
    """

    _true_false_default_ui: AbstractModalTrueFalseDefaultQuestionUI = None

    def get_true_false_default_ui(self):
        return self._true_false_default_ui

    _feedback_ui: AbstractFeedbackUI = None

    def get_feedback_ui(self):
        return self._feedback_ui

    server_routines: GitLabServerRoutines = None

    def get_server_routines(self):
        return self.server_routines

    def __init__(self, server_routines: GitLabServerRoutines,
                 true_false_default_ui: AbstractModalTrueFalseDefaultQuestionUI, feedback_ui: AbstractFeedbackUI):
        self.server_routines = server_routines
        self._true_false_default_ui = true_false_default_ui
        self._feedback_ui = feedback_ui

    @abc.abstractmethod
    def get_typename(self) -> str:
        """The typename of the type we are managing.  e.g. 'my_managed_type'"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_manager_routines(self) -> T:
        """The locally managed type routines."""
        raise NotImplementedError()

    async def push_all_routine(self, group_name: str):
        """
        Pushes all the items from the manager to gitlab.
        :param group_name: The gitlab group name to push to.
        """
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        manager_routines = self.get_local_manager_routines()

        if not RepoExists(local_path):
            await self.get_feedback_ui().error(
                "No local worktree.  You can create an empty one with init_local or use a pull command to get an existing one.")
            return

        repo = git.Repo(local_path)

        if repo.is_dirty(untracked_files=True):
            await self.get_feedback_ui().error("Worktree is dirty.  Aborting.")
            return

        await manager_routines.ExportAllRoutine(local_path)

        for untracked_file in repo.untracked_files:
            if untracked_file.endswith(".json"):
                repo.index.add([untracked_file])
        if repo.is_dirty(untracked_files=True):
            repo.index.commit("exporting all " + self.get_typename() + "(s)")

        # we push to the server even if there was no commit because this is a "push" command.
        remote = create_update_remote(repo, server.get_name(), server_url)
        remote.push("master")

    async def pull_all_routine(self, group_name: str):
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,

                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            remote = create_update_remote(repo, server.get_name(), server_url)
            remote.pull("master")
        else:
            git.Repo.clone_from(server_url, local_path)

        manager_routines = self.get_local_manager_routines()

        await manager_routines.ImportAllRoutine(local_path)

    async def push_routine(self, group_name: str, itemNames: typing.List[str]):
        """
        Pushes named items from the manager to the GitLab server.
        :param group_name: The name of the gitlab group to push to.
        :param itemNames: A list of item names.
        """
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        manager_routines = self.get_local_manager_routines()

        if not RepoExists(local_path):
            await self.get_feedback_ui().error(
                "No local worktree.  You can create an empty one with init_local or use a pull command to get an existing one.")
            return

        repo = git.Repo(local_path)

        if repo.is_dirty(untracked_files=True):
            await self.get_feedback_ui().error("Worktree is dirty.  Aborting.")
            return

        for itemName in itemNames:
            item_path = os.path.join(local_path, itemName + ".json")
            await manager_routines.ExportRoutine(itemName, item_path)

        for untracked_file in repo.untracked_files:
            if untracked_file.endswith(".json"):
                repo.index.add([untracked_file])

        if repo.is_dirty(untracked_files=True):
            repo.git.commit('-a', '-m', '"exporting ' + ','.join(itemNames) + " " + self.get_typename() + '(s)"')

        # we push even if there is no commit.  because it's a 'push' command.

        remote = create_update_remote(repo, server.get_name(), server_url)
        remote.push("master")

    async def pull_routine(self, group_name: str, itemNames: typing.List[str]):
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            if repo.is_dirty(untracked_files=True):
                await self.get_feedback_ui().error("Worktree is dirty.  Aborting.")
                return
            remote = create_update_remote(repo, server.get_name(), server_url)
            remote.pull("master")
        else:
            git.Repo.clone_from(server_url, local_path)

        manager_routines = self.get_local_manager_routines()

        for itemName in itemNames:
            await manager_routines.ImportRoutine(os.path.join(local_path, itemName + ".json"))

    async def delete_local(self, group_name: str):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            if repo.is_dirty(untracked_files=True):
                answer = await self.get_true_false_default_ui().execute("Worktree is dirty. Delete anyway?", "Y", "N",
                                                                        "C", False)
                if answer:
                    del (repo)
                    DeleteLocalRepo(local_path)
            else:
                del (repo)
                DeleteLocalRepo(local_path)
        else:
            DeleteLocalRepo(local_path)

    async def init_local(self, group_name: str):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            await self.get_feedback_ui().error("Repo already exists.  Cannot init.")
            return

        os.makedirs(local_path, exist_ok=True)
        git.Repo.init(local_path)
