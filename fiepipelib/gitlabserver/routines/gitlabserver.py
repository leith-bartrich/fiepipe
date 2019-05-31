import abc
import os
import os.path
import os.path
import pathlib
import typing
import gitlab

import git

from fiepipelib.git.routines.remote import create_update_remote, get_commits_behind, get_commits_ahead, exists
from fiepipelib.git.routines.repo import RepoExists, DeleteLocalRepo, is_in_conflict
from fiepipelib.git.routines.submodules import SetURL,GetURL,ChangeURL
from fiepipelib.gitlabserver.data.gitlab_server import GitLabServer, GitLabServerManager
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedInteractiveRoutines
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
        server_name = self.get_server_name()
        servers = self.get_manager().get_by_name(server_name)
        if len(servers) == 0:
            raise KeyError("No such gitlab server: " + server_name)
        return servers[0]

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

    def provision_fqdn(self, fqdn: str):
        server = self.get_server()
        groupname = self.group_name_from_fqdn(fqdn)
        gitlab_server = gitlab.Gitlab(url="https://" + server.get_hostname(),private_token=server.get_private_token())

        #check for existitng group

        fqdn_group = None
        for group in gitlab_server.groups.list():
            if group.name == groupname:
                fqdn_group = group
                break

        #create if neccesary
        if fqdn_group == None:
            fqdn_group = {'name':groupname,'path':groupname,'visibility':'private','lfs_enabled':True}
            gitlab_server.groups.create(fqdn_group)





T = typing.TypeVar("T", bound=AbstractLocalManagedInteractiveRoutines)


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

    def is_in_conflict(self) -> bool:
        local_repo_path = self.get_local_repo_path()
        repo = git.Repo(local_repo_path)
        return is_in_conflict(repo)

    async def init_submodule_sub_routine(self, feedback_ui:AbstractFeedbackUI, name:str, parent_repo:git.Repo, branch:str ) -> bool:
        server = self.get_server_routines().get_server()
        local_repo_path = self.get_local_repo_path()
        remote_url = self.get_remote_url()

        await feedback_ui.output("Initing submodule: " + local_repo_path + " from: " + remote_url)
        git_cmd = git.Git(local_repo_path)
        submod_init_output = git_cmd.submodule("init",".")
        #submod_init_output = parent_repo.git.submodule("init",local_repo_path)
        await feedback_ui.output(submod_init_output)
        await feedback_ui.output("Updating submodule: " + local_repo_path + " from: " + remote_url)
        ChangeURL(parent_repo,name,remote_url,True)
        submod_update_output = git_cmd.submodule("update",".")
        #submod_update_output = parent_repo.git.submodule("update",local_repo_path)
        await feedback_ui.output(submod_update_output)
        repo = git.Repo(local_repo_path)
        remote_origin = repo.remote("origin")
        remote_origin.set_url(remote_url)
        await feedback_ui.output("Fetching LFS objects: " + local_repo_path + " from: " + remote_url)
        lfs_fetch_output = repo.git.lfs("fetch", remote_url, branch)
        await feedback_ui.output(lfs_fetch_output)
        await feedback_ui.output("Checking out master branch to latest: " + local_repo_path + " from: " + remote_url)
        checkout_output = repo.git.checkout("-f", branch)
        await feedback_ui.output(checkout_output)




    async def pull_sub_routine(self, feedback_ui: AbstractFeedbackUI, branch: str) -> bool:

        server = self.get_server_routines().get_server()
        local_repo_path = self.get_local_repo_path()
        remote_url = self.get_remote_url()

        await feedback_ui.output("Pulling: " + local_repo_path + " from: " + remote_url)

        if RepoExists(local_repo_path):
            repo = git.Repo(local_repo_path)
            remote = create_update_remote(repo, "origin", remote_url)
            remote = create_update_remote(repo, server.get_name(), remote_url)
            assert isinstance(remote, git.Remote)
            await feedback_ui.output(("Pulling " + branch + ": " + local_repo_path + " <- " + remote_url))
            remote.pull(branch)
            return True
        else:
            await feedback_ui.error(
                "Local repository doesn't exist.  Cannot pull.  You might want to clone it or init it?")
            return False

    async def pull_routine(self, feedback_ui: AbstractFeedbackUI):

        await self.pull_sub_routine(feedback_ui)

    async def push_sub_routine(self, feedback_ui: AbstractFeedbackUI, branch: str, fail_on_dirty: bool) -> bool:
        """Meant to be called by other routines.
        Provides feedback.
        Returns True on success, False on failure."""
        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        await feedback_ui.output("Pushing: " + local_path + " to: " + remote_url)

        if not RepoExists(local_path):
            await feedback_ui.error("No local worktree.  You might need to create or pull it first.")
            return False

        repo = git.Repo(local_path)

        if repo.is_dirty(index=True, working_tree=True, untracked_files=True, submodules=True) and fail_on_dirty:
            await feedback_ui.error("Worktree is dirty.  Aborting.")
            return False

        # we push to the server even if there was no commit because this is a "push" command.
        # this works for submodules too, we think.  Maybe?

        remote = create_update_remote(repo, server.get_name(), remote_url)
        assert isinstance(remote, git.Remote)
        await feedback_ui.output("Pushing " + branch + ": " + local_path + " -> " + remote_url)
        remote.push(branch)
        return True

    async def push_lfs_objects_subroutine(self, feedback_ui:AbstractFeedbackUI, branch: str):
        """Push lfs objects to the remote.
        lfs is smart about only pushing objects that need to be pushed.
        Failure will throw.  Therefore, a succesful run of this subroutine guarontees
        lfs objects exist."""
        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        await feedback_ui.output("Pushing LFS objects: " + local_path + " to: " + remote_url)

        if not RepoExists(local_path):
            await feedback_ui.error("No local worktree.  You might need to create or pull it first.")
            return False

        repo = git.Repo(local_path)

        remote = create_update_remote(repo, server.get_name(), remote_url)
        assert isinstance(remote, git.Remote)
        push_output = repo.git.lfs("push",server.get_name(),branch)
        await feedback_ui.output(push_output)
        await feedback_ui.output("Done pushing LFS objects.")


    async def push_routine(self, feedback_ui: AbstractFeedbackUI):
        """Meant to be called direclty by the user.  Dosen't throw on failure."""
        success = await self.push_sub_routine(feedback_ui, "master", True)

    async def remote_exists(self, feedback_ui: AbstractFeedbackUI) -> bool:
        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        repo = git.Repo(local_path)
        server_name = server.get_name()

        await feedback_ui.output("Updating remote " + server_name + " to: " + remote_url)
        create_update_remote(repo, server_name, remote_url)

        ret = exists(repo, server_name)
        if ret:
            await feedback_ui.output("Remote exists.")
        else:
            await feedback_ui.output("Remote doesn't exist.")
        return ret

    async def is_behind_remote(self, feedback_ui: AbstractFeedbackUI) -> bool:

        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        repo = git.Repo(local_path)
        server_name = server.get_name()

        await feedback_ui.output("Updating remote " + server_name + " to: " + remote_url)
        create_update_remote(repo, server_name, remote_url)

        commits_behind = get_commits_behind(repo, "master", server_name)

        ret =  len(commits_behind) != 0
        if ret:
            await feedback_ui.output("Local is behind Remote")
        else:
            await feedback_ui.output("Local is up to date.")
        return ret


    async def is_aheadof_remote(self, feedback_ui: AbstractFeedbackUI) -> bool:

        server = self.get_server_routines().get_server()
        remote_url = self.get_remote_url()
        local_path = self.get_local_repo_path()

        repo = git.Repo(local_path)
        server_name = server.get_name()

        await feedback_ui.output("Updating remote " + server_name + " to: " + remote_url)
        create_update_remote(repo, server_name, remote_url)

        commits_ahead = get_commits_ahead(repo, "master", server_name)

        ret = len(commits_ahead) != 0

        if ret:
            await feedback_ui.output("Local is ahead of Remote")
        else:
            await feedback_ui.output("Remote is not behind")
        return ret

class GitLabManagedTypeRoutines(typing.Generic[T]):
    server_routines: GitLabServerRoutines = None
    _feedback_ui: AbstractFeedbackUI = None

    def __init__(self, feedback_ui: AbstractFeedbackUI, server_routines: GitLabServerRoutines):
        self.server_routines = server_routines
        self._feedback_ui = feedback_ui

    def get_feedback_ui(self):
        return self._feedback_ui

    def get_server_routines(self):
        return self.server_routines

    @abc.abstractmethod
    def get_typename(self) -> str:
        """The typename of the type we are managing.  e.g. 'my_managed_type'"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_local_manager_routines(self) -> T:
        """The locally managed type routines."""
        raise NotImplementedError()

    async def remote_exists(self, group_name:str):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())

        if not RepoExists(local_path):
            await self.get_feedback_ui().error(
                "No local worktree.  You can create an empty one with init_local or use a pull command to get an existing one.")
            return

        repo = git.Repo(local_path)
        return exists(repo,server.get_name())

    async def fetch_master_subroutine(self, group_name: str):
        """Fetches any remote changes but doesn't do anything with them.
        """
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        if not RepoExists(local_path):
            raise RuntimeError("No local worktree.")

        repo = git.Repo(local_path)

        master_branch = None

        # check for branches and create local if needed.
        for branch in repo.heads:
            assert isinstance(branch, git.Head)
            if branch.name == "master":
                master_branch = branch

        if master_branch is None:
            raise RuntimeError("There is no master branch.")

        remote = create_update_remote(repo, server.get_name(), server_url)
        remote.fetch("master")

    async def commit_to_local_subroutine(self, feedback_ui:AbstractFeedbackUI, group_name:str):
        """Ensures the head of the local branch matches the database exactly.
        Which often involves a commit."""
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        manager_routines = self.get_local_manager_routines()
        if not RepoExists(local_path):
            raise RuntimeError("No local worktree.")

        repo = git.Repo(local_path)

        local_branch = None
        master_branch = None

        #check for branches and create local if needed.
        for branch in repo.heads:
            assert  isinstance(branch, git.Head)
            if branch.name == "local":
                local_branch = branch
            if branch.name == "master":
                master_branch = branch

        if master_branch is None:
            raise RuntimeError("There is no master branch.")

        if local_branch is None:
            await feedback_ui.output("Creating local branch from master.")
            branch_output = repo.git.branch("local","master")
            await feedback_ui.output(branch_output)
            await feedback_ui.output("Branch created.")
            local_branch = git.Head(repo,"local")

        #check out local
        local_branch.checkout(force=True)

        #we clear the dir of items
        items = os.listdir(local_path)
        for item in items:
            if item.endswith(".json"):
                os.remove(os.path.join(local_path,item))

        #then we export from the db
        await manager_routines.ExportAllRoutine(local_path)

        #do an add
        add_output = repo.git.add("--all")
        await feedback_ui.output(add_output)

        #do a commit
        if repo.is_dirty():
            commit_output = repo.git.commit("-a","-m","\"commiting db to local.\"")
            await feedback_ui.output(commit_output)

    async def merge_local_to_master_subroutine(self, feedback_ui:AbstractFeedbackUI, group_name:str):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if not RepoExists(local_path):
            #nothing to merge.  So, done.
            return

        repo = git.Repo(local_path)

        local_branch = None
        master_branch = None

        #check for branches.
        for branch in repo.heads:
            assert  isinstance(branch, git.Head)
            if branch.name == "local":
                local_branch = branch
            if branch.name == "master":
                master_branch = branch

        if master_branch is None:
            raise RuntimeError("There is no master branch.")

        if local_branch is None:
            #nothing to merge.  So, done.
            return

        #checkout master
        master_branch.checkout(force=True)

        if repo.is_dirty():
            raise RuntimeError("Checkout of master is dirty.  Won't continue.")

        #we merge local into master.
        await feedback_ui.output("Merging local into master.")
        merge_output = repo.git.merge("--no-edit","local")
        await feedback_ui.output(merge_output)

        #repo.index.merge_tree(local_branch)
        if is_in_conflict(repo):
            raise RuntimeError("Conflicts found after merge.  Manual resolution required.  Won't continue.")
        if repo.is_dirty():
            repo.index.commit("Merged local changes to master.")

        #if we got here, then we succesfully merged from local to master.  We merge back, to make future merges easier.
        local_branch.checkout(force=True)

        if repo.is_dirty():
            raise RuntimeError("Checkout of local is dirty.  Won't continue.")

        await feedback_ui.output("Merging master back into local.")
        merge_output = repo.git.merge("--no-edit","master")
        await feedback_ui.output(merge_output)

        #repo.index.merge_tree(master_branch)
        if is_in_conflict(repo):
            raise RuntimeError("Conflicts found after merging master back to local.  Manual resolution required.  Won't continue.")
        if repo.is_dirty():
            repo.index.commit("Merged master back to local.")

        #what we've done is as follows:
        #local branch consists of local versions, stacked on a recent master commit.
        #the merge to master, will hopefully





    async def import_from_master_subroutine(self, feedback_ui:AbstractFeedbackUI, group_name:str):
        """This overwrites the db with the master branch.  Therefore, we delete and replace local with master as well.
        This helps track and merge changes.
        """
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if not RepoExists(local_path):
            raise RuntimeError("No local worktree.")

        repo = git.Repo(local_path)

        master_branch = None

        #check for branches and create local if needed.
        for branch in repo.heads:
            assert  isinstance(branch, git.Head)
            if branch.name == "master":
                master_branch = branch

        if master_branch is None:
            raise RuntimeError("There is no master branch.")

        #check out master
        master_branch.checkout(force=True)

        if repo.is_dirty():
            raise RuntimeError("Master branch is dirty after checkout.  Won't import dirty data to db.")


        manager_routines = self.get_local_manager_routines()

        #clear out the manager before importing
        for item in manager_routines.GetAllItems():
            name = manager_routines.ItemToName(item)
            await manager_routines.DeleteRoutine(name)

        await manager_routines.ImportAllRoutine(local_path)

        #if we got here, we succesfully imported from master.
        #now we kill the local branch completely and create it from master
        for branch in repo.heads:
            assert  isinstance(branch, git.Head)
            if branch.name == "local":
                git.Head.delete(repo,"local",force=True)
                branch_output = repo.git.branch("local", "master")
                await feedback_ui.output(branch_output)

    async def push_commits_subroutine(self, feedback_ui, group_name):
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())

        repo = git.Repo(local_path)

        # we push to the server even if there was no commit because this is a "push" command.  Server could be behind for other reasons.
        remote = create_update_remote(repo, server.get_name(), server_url)
        #this could fail if you don't have permission to write container changes.  And that's okay because securityis handled by gitlab after all.
        remote.push("master")


    async def safe_merge_update_routine(self, feedback_ui:AbstractFeedbackUI, group_name:str):
        """
        This routine does a 'safe' merge of local changes, and update of remote changes.
        """

        # sanity check.  What if the local db is from a different server (location)?
        # answers:
        #   if the containers asset is the same, repo, it doesn't matter.
        #   if the containers asset is a different repo, then a merge local to master should fail.


        # we commit to local.
        await self.commit_to_local_subroutine(feedback_ui,group_name)
        # If there were no changes, then there is no commit made.
        # Therefore, we either have (as head):
        #   an existing master commit
        #   a series of local commits on top of a master commit


        #we merge local to master
        await self.merge_local_to_master_subroutine(feedback_ui, group_name)
        #if there are no local commits, this simply succeeds without doing anything.
        #also, local is now updated master's newest head commit, guaronteed.

        #to this point, we have not done anything with remotes

        #we pull in further changes to master from remote
        await self.fetch_master_subroutine(group_name)


        #we export a newly updated and merged master to the db
        #this blows away the local branch and re-creates it from master
        await self.import_from_master_subroutine(feedback_ui,group_name)

        #last, we push any commits that we can.
        await self.push_commits_subroutine(feedback_ui, group_name)

    async def checkout_routine(self, feedback_ui:AbstractFeedbackUI, group_name:str):
        """Does a fresh checkout of the master branch from remote.  Blows away existing repo and db items."""
        server = self.get_server_routines().get_server()
        server_url = self.get_server_routines().remote_path_for_entity_registry(group_name=group_name,
                                                                                type_name=self.get_typename())
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            #blow it away
            DeleteLocalRepo(local_path)

        await self.get_feedback_ui().output("Cloning from: " + server_url)
        git.Repo.clone_from(server_url, local_path)
        await self.import_from_master_subroutine(feedback_ui,group_name)




    def is_conflicted(self, group_name: str) -> bool:
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            return is_in_conflict(repo)


    async def init_local(self, group_name: str):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            await self.get_feedback_ui().error("Repo already exists.  Cannot init.")
            return

        os.makedirs(local_path, exist_ok=True)
        git.Repo.init(local_path)

    async def delete_local(self, group_name: str, fail_on_dirty=False) -> bool:
        """Returns true of deleted or not there.  False if deletion failed."""
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            if repo.is_dirty(untracked_files=True):
                if not fail_on_dirty:
                    del (repo)
                    DeleteLocalRepo(local_path)
                    return True
                else:
                    return False
            else:
                del (repo)
                DeleteLocalRepo(local_path)
                return True
        else:
            DeleteLocalRepo(local_path)
            return True



class GitLabManagedTypeInteractiveRoutines(GitLabManagedTypeRoutines[T]):
    """Abstract Routines for sharing Local Managed Types through GitLab.

    The scope of the locally managed types comes from the local type manager returned from the
    'get_locally_managed_routines' method.

    e.g. if the manager is FQDN scoped, then pushes will automatically by FQDN scoped
    because a call to "getall" in the manager will automatically enforce the scope.  Similarly, a
    find by name will also be scoped by the manager.
    """

    async def delete_local_interactive_routine(self, group_name: str,
                                               dirty_ui: AbstractModalTrueFalseDefaultQuestionUI):
        server = self.get_server_routines().get_server()
        local_path = self.get_server_routines().local_path_for_type_registry(server.get_name(), group_name,
                                                                             self.get_typename())
        if RepoExists(local_path):
            repo = git.Repo(local_path)
            if repo.is_dirty(untracked_files=True):
                answer = await dirty_ui.execute("Worktree is dirty. Delete anyway?", "Y", "N", "C", False)
                if answer:
                    del (repo)
                    DeleteLocalRepo(local_path)
            else:
                del (repo)
                DeleteLocalRepo(local_path)
        else:
            DeleteLocalRepo(local_path)
