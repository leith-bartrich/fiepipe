import abc
import typing

import git

from fiepipelib.assetstructure.routines.structure import AbstractAssetBasePath, BT, AutoManageResults, \
    AbstractRootBasePath, AutoCreateResults, AbstractPath
from fiepipelib.automanager.data.localconfig import LegalEntityConfig, LegalEntityMode
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fiepipelib.enum import get_worse_enum
from fieui.FeedbackUI import AbstractFeedbackUI


class AbstractDesktopProjectRootBasePath(AbstractRootBasePath[BT], typing.Generic[BT], abc.ABC):
    """A convenience base path base class for a Desktop style project root.
    Assumes distributed project system, contributed to and pulled by many
    different desktop users across multiple sites/networks/segments/planets/solar-systems/etc."""

    def get_sub_desktop_asset_basepaths(self) -> typing.List["AbstractDesktopProjectAssetBasePath"]:
        ret = []
        subs = self.get_sub_basepaths()
        for sub in subs:
            if isinstance(sub, AbstractDesktopProjectAssetBasePath):
                ret.append(sub)
        return ret

    async def automanager_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                  container_config: ContainerAutomanagerConfigurationComponent) -> AutoManageResults:
        # We can assume we've (the root) just been updated by the automanager and that we're not in conflicted.
        # But that is all.  This means we don't need to 'pull' from remote.
        #
        # we need to create, add and commit missing structure.
        # we need to report (and fail) dirt that's not handled by structure, and isn't just a submodule version update.
        # we should push those commits.
        # we need to then allow desktop assets to automanage recursively.
        # probably, we'll end up with dirty submodules.  And we should ignore them.  Any sort of "publish" of an asset
        # will push versions.  We don't need to do that here.

        # return results. best possible status.  we degrade as we move along.
        ret = AutoManageResults.CLEAN

        if entity_config.get_mode() == LegalEntityMode.NONE:
            # for lack of a better respose, we don't know.
            return AutoManageResults.PENDING

        if entity_config.get_mode() == LegalEntityMode.USER_WORKSTATION:

            # first, create static structure.
            create_status = AutoCreateResults.NO_CHANGES

            for subpath in self.get_subpaths():
                if not subpath.exists():
                    # this is recursive....
                    subpath_ret = await subpath.automanager_create(feedback_ui, entity_config, container_config)
                    create_status = get_worse_enum(create_status, subpath_ret)
                    # catch a failure.

            if create_status == AutoCreateResults.CANNOT_COMPLETE:
                await feedback_ui.output(
                    "Canceling further auto-management of this storage root due to a subpath failing to create.")
                return AutoManageResults.CANNOT_COMPLETE

            # we need to check for working-copy dirt that's not in the index and fail based on it.
            is_dirty = self.is_dirty(False, True, True, False)
            if is_dirty:
                await feedback_ui.output("Root worktree is dirty.  Cannot auto-commit.  Canceling further auto-management.")
                await feedback_ui.output(self.get_path())
                return AutoManageResults.CANNOT_COMPLETE

            # Commit the index if it needs it.
            # this will be pushed next time through.
            index_dirty = self.is_dirty(True, False, False, False)
            if index_dirty:
                self.get_routines().get_repo().index.commit("Auto-manager commit of changed structure.")

            # we move into our child logic.

            pre_ret = await self.pre_child_assets_automanage_routine(feedback_ui)

            ret = get_worse_enum(ret, pre_ret)

            if ret == AutoManageResults.CANNOT_COMPLETE:
                await feedback_ui.error(
                    "Pre-children auto-management routine failed.  Canceling child auto-management.")
                return ret

            children = self.get_sub_desktop_asset_basepaths()

            for child in children:
                child_ret = await child.automanage_routine(feedback_ui,entity_config,container_config)
                ret = get_worse_enum(ret, child_ret)

            if ret == AutoManageResults.CANNOT_COMPLETE or ret == AutoManageResults.PENDING:
                await feedback_ui.error(
                    "At least one child's auto-management routine failed or is pending.  Canceling post-child auto-management.")
                return ret

            post_ret = await self.post_child_assets_automanage_routine(feedback_ui)

            ret = get_worse_enum(ret, post_ret)

            return ret

    async def pre_child_assets_automanage_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoManageResults:
        """Called before automanaging children.  Feel free to override but do call super()"""
        return AutoManageResults.CLEAN

    async def post_child_assets_automanage_routine(self, feedback_ui: AbstractFeedbackUI) -> AutoManageResults:
        """Called after automanaging children.  Feel free to override but do call super()"""
        return AutoManageResults.CLEAN

BDT = typing.TypeVar("BDT", bound=AbstractDesktopProjectRootBasePath)

class AbstractDesktopProjectAssetBasePath(AbstractAssetBasePath[BDT], typing.Generic[BDT], abc.ABC):
    """A convenience base path base class for Desktop style asset in a project root.
    Assumes distributed project system, contributed to and pulled by many
    different desktop users across multiple sites/networks/segments/planets/solar-systems/etc."""

    def get_sub_desktop_asset_basepaths(self) -> typing.List["AbstractDesktopProjectAssetBasePath"]:
        ret = []
        subs = self.get_sub_basepaths()
        for sub in subs:
            if isinstance(sub, AbstractDesktopProjectAssetBasePath):
                ret.append(sub)
        return ret

    async def automanage_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                 container_config: ContainerAutomanagerConfigurationComponent) -> AutoManageResults:
        """
        Override and call this to modify automanage logic.  This implementation handles children.

        Usually you don't want to override this, rather, you want to override the pre_children_automanage_routine
        and post_children_automanage_routine instead.

        Though one thing you could do by overriding this routine, is execute logic before and after even those routines
        are called.
        """

        # We can't assume anything.  We might not even be checked out or init'd

        if entity_config.get_mode() == LegalEntityMode.NONE:
            # for lack of a better respose, we don't know.
            return AutoManageResults.PENDING

        elif entity_config.get_mode() == LegalEntityMode.USER_WORKSTATION:
            # we need to determine if we're checked out.
            # we need to create, add and commit missing structure.
            # we need to allow desktop assets to automanage recursively.
            # probably, we'll end up with dirty submodules.  And we should ignore them.  Any sort of "publish" of an asset
            # will push versions.  We don't need to do that here.

            ret = AutoManageResults.CLEAN
            routines = self.get_routines()
            routines.load()

            if not routines.is_init():
                # if we-re not checked out, then we're okay.  It's fine to not have an asset checked out.  That just means
                # it's opting out of auto-management for now.
                return AutoManageResults.CLEAN

            # children and automanagement.

            pre_ret = await self.pre_children_automanage_routine(feedback_ui, entity_config, container_config)
            ret = get_worse_enum(ret, pre_ret)

            if ret == AutoManageResults.CANNOT_COMPLETE or ret == AutoManageResults.PENDING:
                await feedback_ui.warn(
                    "Pre-children auto-management failed or is pending.  Canceling further auto-management.")
                return ret

            children = self.get_sub_desktop_asset_basepaths()
            for child in children:
                child_status = await child.automanage_routine(feedback_ui, entity_config, container_config)
                ret = get_worse_enum(ret, child_status)

            if ret == AutoManageResults.CANNOT_COMPLETE or ret == AutoManageResults.PENDING:
                await feedback_ui.warn(
                    "At least one child auto-management failed or is pending.  Canceling further auto-management.")
                return ret

            post_ret = await self.post_children_automanage_routine(feedback_ui, entity_config, container_config, ret)
            ret = get_worse_enum(ret, post_ret)

            if ret == AutoManageResults.CANNOT_COMPLETE or ret == AutoManageResults.PENDING:
                await feedback_ui.warn(
                    "Post-children auto-management failed or is pending.  Canceling further auto-management.")
                return ret

            return ret

        else:
            await feedback_ui.error("Unsupported entity auto-manager mode.")
            return AutoManageResults.CANNOT_COMPLETE

    async def pre_children_automanage_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                              container_config: ContainerAutomanagerConfigurationComponent) -> AutoManageResults:
        """
        Override and call this to execute automanage logic before children are automanaged.
        This implementation calls structure creation and auto-commits any changes that
        are made as a result.  If untracked or worktree changes exist, it skips the
        auto-commit.

        Auto-creation is called before children, so than any children that are auto-created, are also
        auto-managed.
        """
        ret = AutoManageResults.CLEAN

        if entity_config.get_mode() == LegalEntityMode.USER_WORKSTATION:

            # first, any conflict is a problem.
            is_conflicted = self.is_conflicted()
            if is_conflicted:
                await feedback_ui.warn("Asset is in conflict: " + self.get_routines().abs_path)
                await feedback_ui.warn("Cannot auto-manage further.")
                return AutoManageResults.CANNOT_COMPLETE


            remote_exists = self.remote_exists()

            if remote_exists:

                # we need to detect and push if we're ahead, as early as possible, to hopefully avoid conflicts later.
                # this is optimistic or eventual convergence logic.
                remote_is_ahead = self.remote_is_ahead()
                remote_is_behind = self.remote_is_behind()

                if remote_is_behind and not remote_is_ahead:
                    success = await self.get_gitlab_asset_routines().push_sub_routine(feedback_ui, 'master', False)
                    # we don't care about success or failure here.  We'll check this again in post-children.
            else:

                #we push it early if it doesn't exist yet.
                success = await self.get_gitlab_asset_routines().push_sub_routine(feedback_ui, 'master', False)

            # if we're unforunate enough to be both ahead and behind, that'll be caught later in post-children.
            # children don't care if their parent might conflict in a bit.  We need to resolve them first.

            # catch a detached head
            is_detached = self.is_detached()

            if is_detached:
                await feedback_ui.error("Asset is detached from head.")
                await feedback_ui.error("It's dangerous to continue as we could diverge.  User intervention required.")
                await feedback_ui.error(
                    "Make sure any children with unpublished commits get pushed, before blindly updating this asset.")
                return AutoManageResults.CANNOT_COMPLETE

            # structure creation
            create_status = AutoCreateResults.NO_CHANGES

            for subpath in self.get_subpaths():
                if not subpath.exists():
                    # this is recursive....
                    subpath_ret = await subpath.automanager_create(feedback_ui, entity_config, container_config)
                    create_status = get_worse_enum(create_status, subpath_ret)
                    # catch a failure.

            if create_status == AutoCreateResults.CANNOT_COMPLETE:
                await feedback_ui.output(
                    "Canceling further auto-management of this storage asset due to a subpath failing to create.")
                return AutoManageResults.CANNOT_COMPLETE

            if create_status == AutoCreateResults.CHANGES_MADE:
                await feedback_ui.output("Asset structure creation reports changes were made.")
                if self.is_dirty(True, False, False, False):
                    await feedback_ui.output("Index is dirty.")
                    if self.is_dirty(False, True, True, False):
                        await feedback_ui.output(
                            "The worktree is dirty or there are untracked files.  Cannot auto-commit.")
                        # worktree or untracked files dirty
                        ret = get_worse_enum(ret, AutoManageResults.DIRTY)
                    else:
                        await feedback_ui.output("The worktree is clean.  Attempting auto-commit.")
                        repo = self.get_routines().get_repo()
                        try:
                            repo.index.commit("Auto-manager git-asset structure auto-commit")
                        except git.GitCommandError as err:
                            await feedback_ui.error("Error on commit:")
                            await feedback_ui.error(err.stdout)
                            return AutoManageResults.CANNOT_COMPLETE
                else:
                    await feedback_ui.output("Index is clean however.  No commit necessary.")
                    ret = get_worse_enum(ret, AutoManageResults.CLEAN)

            self_is_dirty = self.is_dirty(True, True, True, False)

            if self_is_dirty:
                return get_worse_enum(ret, AutoManageResults.DIRTY)
            else:
                return get_worse_enum(ret, AutoManageResults.CLEAN)
        else:
            await feedback_ui.error("Unsupported entity auto-manager mode.")
            return AutoManageResults.CANNOT_COMPLETE

    async def post_children_automanage_routine(self, feedback_ui: AbstractFeedbackUI, entity_config: LegalEntityConfig,
                                               container_config: ContainerAutomanagerConfigurationComponent,
                                               children_results: AutoManageResults) -> AutoManageResults:
        """
        Override and call this to execute automanage logic after children are auto-managed.  This implementation
        handles the pulling and pushing of commits for you.  Ideally, you have already created commits before it is called.

        Ideally, you'd execute structure management in the overridden method, just before calling this super method.  That way,
        you can use the children_results to understand if its safe to do things to this structure, make changes, commit them, and let
        the super method handle the pushing and pulling at that point.

        If you reach an error condition you can always return AutoMangeResults.CANNOT_COMPLETE and expect no further
        processing will be done.

        Or, if you reach a condition where another loop of the auto-management should be run to attempt resolution, you can return AutoMangeResults.PENDING

        You should not call the super method in these cases.
        """

        ret = AutoManageResults(children_results)

        # all children have been run and are either clean or dirty or have unpublished_commits.
        if entity_config.get_mode() == LegalEntityMode.USER_WORKSTATION:

            # next, we need to determine if the user is 'working' on this asset or not.
            # they're 'working' on it, if it's dirty, or if children are dirty.

            self_is_dirty = self.is_dirty(True, True, True, False)
            children_dirty = (children_results == AutoManageResults.DIRTY) or (
                        children_results == AutoManageResults.DIRTY_AND_UNPUBLISHED_COMMITS)
            is_working_on = self_is_dirty or children_dirty
            children_unpublished_commits = (children_results == AutoManageResults.UNPUBLISHED_COMMITS) or (
                        children_results == AutoManageResults.DIRTY_AND_UNPUBLISHED_COMMITS)

            remote_is_behind = self.remote_is_behind()
            remote_is_ahead = self.remote_is_ahead()
            is_detached = self.is_detached()
            gitlab_asset_routines = self.get_gitlab_asset_routines()

            # detached logic spercedes other logic.
            # in desktop mode, it's not okay to be detached. We either safely fix it, or error out.
            if is_detached:
                await feedback_ui.output("Asset is detached from 'master' head.")
                if self_is_dirty:
                    await feedback_ui.error("Asset is dirty.")
                    await feedback_ui.warn(
                        "You are in danger of divergence because you are working on a detached head.")
                    await feedback_ui.warn("This cannot be automatically resolved.  User intervention is required.")
                    return AutoManageResults.CANNOT_COMPLETE
                else:
                    await feedback_ui.output("Asset is clean.")
                    if children_unpublished_commits:
                        await feedback_ui.error("Children have unpublished commits.")
                        await feedback_ui.error(
                            "Cannot safely resolve automatically because we might lose childrens' commits.  User intervention is required.")
                        return AutoManageResults.CANNOT_COMPLETE
                    elif children_dirty:
                        await feedback_ui.error("Children are dirty.")
                        await feedback_ui.error(
                            "Cannot safely resolve automatically because we might lose childrens' changes in progress.  User invervention is required.")
                        return AutoManageResults.CANNOT_COMPLETE
                    else:
                        await feedback_ui.output("Children have no unpublished commits and are clean.")
                        await feedback_ui.output("Attempting to automatically checkout 'HEAD'")
                        repo = git.Repo(gitlab_asset_routines.get_local_repo_path())
                        try:
                            output = repo.git.checkout("master")
                            await feedback_ui.output(output)
                        except git.GitCommandError as err:
                            await feedback_ui.error("There was an error checking out the master branch.")
                            await feedback_ui.error(err.stderr)
                            return AutoManageResults.CANNOT_COMPLETE
                        if self.is_conflicted():
                            await feedback_ui.error("Checkout resulted in conflict.  User intervention required.")
                            return AutoManageResults.CANNOT_COMPLETE
                        else:
                            # we succesfully updated.
                            await feedback_ui.output("Up to date and clean at head.")
                            ret = get_worse_enum(ret, AutoManageResults.CLEAN)

            # We always push commits if we can.  Eventual convergence.
            if remote_is_behind and not remote_is_ahead:
                await feedback_ui.output("Local Asset is ahead of remote.  Pushing commits.")
                push_success = await gitlab_asset_routines.push_sub_routine(feedback_ui, 'master', False)
                # A failure here downgrades the return, but we continue on.
                if not push_success:
                    await feedback_ui.output("Failed to push.  But this is not fatal to auto-management.")
                    if self_is_dirty:
                        ret = get_worse_enum(ret, AutoManageResults.DIRTY_AND_UNPUBLISHED_COMMITS)
                    else:
                        ret = get_worse_enum(ret, AutoManageResults.UNPUBLISHED_COMMITS)

            if remote_is_ahead:
                await feedback_ui.output("Remote Asset is ahead of local.")
                if is_working_on:
                    await feedback_ui.warn(
                        "This asset is being worked on.  User may want to merge in changes manually.")
                    if children_unpublished_commits:
                        await feedback_ui.warn(
                            "Its children have unpublished commits and that should be resolved before merging/pulling this asset.")
                    if children_dirty:
                        await feedback_ui.warn(
                            "Its children are dirty and should be resolved before merging/pulling this asset.")
                    ret = get_worse_enum(ret, AutoManageResults.DIRTY)
                else:
                    await feedback_ui.output("Neither this asset nor its children are being worked on.")
                    await feedback_ui.output("Attempting to pull from remote.")
                    pull_success = await gitlab_asset_routines.pull_sub_routine(feedback_ui, 'master')
                    if self.is_conflicted():
                        await feedback_ui.warn("Asset is conflicted after pull.  Cancelling further auto-management.")
                        return AutoManageResults.CANNOT_COMPLETE
                    if not pull_success:
                        await feedback_ui.warn("Pull failed. Continuing auto-management.")
                        # no change to ret
                    else:
                        if remote_is_behind:
                            await feedback_ui.output("Remote was also behind.  Attempting to push now merged commits.")
                            push_success = await gitlab_asset_routines.push_sub_routine(feedback_ui, 'master', False)
                            if push_success:
                                await feedback_ui.output("Auto merge and push successful.  Up to date and clean.")
                                ret = get_worse_enum(ret, AutoManageResults.CLEAN)
                            else:
                                await feedback_ui.output(
                                    "Merge succeeded but push failed.  Continuing auto-management.")
                                ret = get_worse_enum(ret, AutoManageResults.UNPUBLISHED_COMMITS)
                        else:
                            await feedback_ui.output("Up to date and clean.")
                            ret = get_worse_enum(ret, AutoManageResults.CLEAN)

                # if we get here, we've pulled and pushed (if neccesary) and we're not conflicted.

                # if we were neither ahead nor behind, we just need to downgrade based on our dirt level.
                if self_is_dirty:
                    ret = get_worse_enum(ret, AutoManageResults.DIRTY)
                else:
                    ret = get_worse_enum(ret, AutoManageResults.CLEAN)

            # done auto-managing desktop asset.
            return ret
        else:
            await feedback_ui.error("Unsupported entity auto-manager mode.")
            return AutoManageResults.CANNOT_COMPLETE

