import typing

from fiepipelib.gitstorage.data.localstoragemapper import get_local_storage_mapper
from fiepipelib.gitstorage.routines.gitlab_server import GitLabGitRootRoutines, GitLabGitAssetRoutines
from fiepipelib.shells.AbstractShell import AbstractShell


class Shell(AbstractShell):

    def get_plugin_names_v1(self) -> typing.List[str]:
        ret = super(Shell, self).get_plugin_names_v1()
        ret.append("gitroot_gitlab_server_shell")
        return ret

    def get_prompt_text(self) -> str:
        routines = self.get_routines()
        remote_url = routines.get_remote_url()
        return self.prompt_separator.join(['fiepipe', 'gitlab_server_gitroot', remote_url])

    _routines: GitLabGitRootRoutines = None

    def get_routines(self) -> GitLabGitRootRoutines:
        return self._routines

    def __init__(self, routines: GitLabGitRootRoutines):
        self._routines = routines
        super().__init__()

    def do_push_root(self, args):
        """
        Pushes the local root to the GitLab server.

        Usage: push_root
        """
        routines = self.get_routines()
        self.do_coroutine(routines.push(self.get_feedback_ui()))

    def do_pull_root(self, args):
        """
        Pulls the root from the GitLab server to the local root.

        Usage: pull_root
        """
        routines = self.get_routines()
        self.do_coroutine(routines.pull(self.get_feedback_ui()))

    def do_clone_root(self, args):
        """Clones from the GitLab server to the local root.

        Usage clone_root
        """
        routines = self.get_routines()
        self.do_coroutine(routines.clone(self.get_feedback_ui()))

    def backing_volume_complete(self, text, line, begidx, endidx):
        mapper = get_local_storage_mapper()
        backing_vols = mapper.GetMountedBackingStorage()
        ret = []
        for vol in backing_vols:
            if vol.GetName().startswith(text):
                ret.append(vol.GetName())
        return ret

    complete_clone_split = backing_volume_complete

    def do_clone_root_split(self, args):
        """Clones from the GitLab server to the local root, using the given backing volume for repository storage.

        Usage: clone_root_split [vol]

        arg vol:  The name of the local backing volume to use."""

        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No volume specified.")
            return

        mapper = get_local_storage_mapper()
        vol = mapper.GetMountedBackingStorageByName(args[0])

        routines = self.get_routines()
        self.do_coroutine(routines.clone_split(vol, self.get_feedback_ui()))

    def do_pull_whole_consistent(self, args):
        """Does an update/pull to a consistent full tree of all assets, checking out new
        ones as needed.

        It's possible some assets have newer versions commited than what will be checked out.
        But this command will do a pull to the same versions every time, for a given root
        version/state.

        Useful to get a branch as it was when the committer did their commit.  Or get a tree
        in a deterministic fashion.

        Usage: pull_whole_consistent
        """
        routines = self.get_routines()
        routines.pull(self.get_feedback_ui())
        for asset_routines in routines.get_all_asset_routines(recursive=False):
            assert isinstance(asset_routines, GitLabGitAssetRoutines)
            self.do_coroutine(asset_routines.update_branch(latest=False, init=True, feedback_ui=self.get_feedback_ui()))

    def do_pull_whole_latest(self, args):
        """Does an update/pull to the latest tree of all assets, checking out new ones as needed.
        The tree that this checks out is bleeding edge latest and greatest, and parts might
        be newer than when the last commit of their parents was made.

        Useful to get everyone's latest versions before updating your part.

        Usage: pull_whole_latest
        """
        routines = self.get_routines()
        routines.pull(self.get_feedback_ui())
        for asset_routines in routines.get_all_asset_routines(recursive=False):
            assert isinstance(asset_routines, GitLabGitAssetRoutines)
            self.do_coroutine(asset_routines.update_branch(latest=True, init=True, feedback_ui=self.get_feedback_ui()))

    def do_pull_existing_latest(self, args):
        """Does an update/pull to the latest tree of all assets, skipping those not checked out.
        The tree that this checks out is bleeding edge latest and greatest, and parts might
        be newer than when the last commit of their parents was made.

        Useful to get everyone's latest versions before updating your part, without pulling the deeper
        parts of the tree you don't need.

        Usage: pull_existing_latest
        """
        routines = self.get_routines()
        self.do_coroutine(routines.pull(self.get_feedback_ui()))
        for asset_routines in routines.get_all_asset_routines(recursive=False):
            assert isinstance(asset_routines, GitLabGitAssetRoutines)
            self.do_coroutine(asset_routines.update_branch(latest=True, init=False, feedback_ui=self.get_feedback_ui()))

    def do_push_existing(self, args):
        """Does a push of all current assets and then the root.  Children go before parents.

        Used to publish your changes to the tree.
        """
        routines = self.get_routines()
        for asset_routines in routines.get_all_asset_routines(recursive=False):
            assert isinstance(asset_routines, GitLabGitAssetRoutines)
            self.do_coroutine(asset_routines.push_branch(self.get_feedback_ui()))
        self.do_coroutine(routines.push(self.get_feedback_ui()))

    def asset_complete(self, text, line, begidx, endidx):
        routines = self.get_routines()
        all_asset_routines = routines.get_all_asset_routines(recursive=True)
        ret = []
        for asset_routines in all_asset_routines:
            assert isinstance(asset_routines, GitLabGitAssetRoutines)
            subpath = asset_routines._working_asset.GetSubmodule().path
            if subpath.startswith(text):
                ret.append(subpath)
            id = asset_routines._working_asset.GetAsset().GetID()
            if id.startswith(text):
                ret.append(id)
        return ret

    def get_asset_routines(self, pathorid: str) -> GitLabGitAssetRoutines:
        routines = self.get_routines()
        all_asset_routines = routines.get_all_asset_routines(recursive=True)
        for routines in all_asset_routines:
            assert isinstance(routines, GitLabGitAssetRoutines)
            if routines._working_asset.GetSubmodule().path == pathorid:
                return routines
            if routines._working_asset.GetAsset().GetID() == pathorid:
                return routines
        raise LookupError(pathorid)

    complete_checkout_asset = asset_complete

    def do_checkout_asset(self, args):
        """Checks out an asset from gitlab.

        Usage: checkout_asset [subpath]

        arg subpath: The subpath of the asset to checkout.
        """

        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No subpath given.")
            return

        asset_routines = self.get_asset_routines(args[0])
        self.do_coroutine(asset_routines.init(self.get_feedback_ui()))
        self.poutput(
            "The asset will be at the version it was when the parent asset/root was last committed (detached head).")
        do_update = self.do_coroutine(
            self.get_true_false_default_question_modal_ui().execute("Do you want to update to the latest version?",
                                                                    default=True))
        if do_update:
            self.do_coroutine(asset_routines.update(self.get_feedback_ui(), True, False))

    complete_checkout_branch = asset_complete

    def do_checkout_branch(self, args):
        """Checks out an asset branch from gitlab.

        Usage: checkout [subpath]

        arg subpath: The subpath of the asset to checkout."""

        args = self.parse_arguments(args)
        if len(args) == 0:
            self.perror("No subpath given.")
            return

        asset_routines = self.get_asset_routines(args[0])
        self.do_coroutine(asset_routines.init_branch(self.get_feedback_ui()))
        self.poutput(
            "The assets will be at the versions they were when their parent assets/root was last committed (detached heads).")
        do_update = self.do_coroutine(self.get_true_false_default_question_modal_ui().execute(
            "Do you want to update them to the latest versions?", default=True))
        if do_update:
            self.do_coroutine(asset_routines.update_branch(self.get_feedback_ui(), latest=True, init=False))
