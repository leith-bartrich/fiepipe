import abc
import asyncio
import typing
import traceback
import git
import pkg_resources
import sys

from fiepipelib.automanager.data.localconfig import LegalEntityConfig, \
    LegalEntityConfigManager, LegalEntityMode
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfigurationManager
from fiepipelib.container.shared.data.container import LocalContainerManager
from fiepipelib.container.shared.routines.gitlabserver import GitlabManagedContainerRoutines
from fiepipelib.container.shared.routines.manager import FQDNContainerManagementRoutines
from fiepipelib.git.routines.repo import RepoExists
from fiepipelib.gitlabserver.data.gitlab_server import GitLabServerManager
from fiepipelib.gitlabserver.routines.gitlabserver import GitLabServerRoutines
from fiepipelib.gitstorage.data.git_root import SharedGitRootsComponent
from fiepipelib.gitstorage.routines.gitlab_server import GitLabFQDNGitRootRoutines
from fiepipelib.gitstorage.routines.gitroot import GitRootRoutines
from fiepipelib.legalentity.registry.data.registered_entity import localregistry
from fiepipelib.locallymanagedtypes.routines.localmanaged import AbstractLocalManagedRoutines, \
    AbstractLocalManagedInteractiveRoutines
from fiepipelib.localuser.routines.localuser import get_local_user_routines
from fieui.AbstractEnumChoiceModal import AbstractEnumChoiceModal
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.InputDefaultModalUI import AbstractInputDefaultModalUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI
from fiepipelib.container.local_config.data.localcontainerconfiguration import LocalContainerConfiguration

class LegalEntityRoutines(AbstractLocalManagedRoutines[LegalEntityConfig]):

    def GetManager(self) -> LegalEntityConfigManager:
        return LegalEntityConfigManager(get_local_user_routines())

    def GetAllItems(self) -> typing.List[LegalEntityConfig]:
        return self.GetManager().GetAll()

    def ItemToName(self, item: LegalEntityConfig) -> str:
        return item.get_fqdn()

    def GetItemByName(self, name: str) -> LegalEntityConfig:
        return self.GetManager().get_by_fqdn(name)[0]

    async def DeleteRoutine(self, name: str):
        self.GetManager().delete_by_fqdn(name)


class LegalEntityModeChoiceUI(AbstractEnumChoiceModal[LegalEntityMode], abc.ABC):
    pass


class GitlabServerNameUI(AbstractInputDefaultModalUI[str]):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        return (True, v)


class LegalEntityInteractiveRoutines(LegalEntityRoutines, AbstractLocalManagedInteractiveRoutines[LegalEntityConfig]):
    _legal_entity_mode_ui: LegalEntityModeChoiceUI = None
    _gitlab_server_ui: GitlabServerNameUI = None
    _active_ui: AbstractModalTrueFalseDefaultQuestionUI = None

    def __init__(self, feedback_ui: AbstractFeedbackUI, legal_entity_mode_ui: LegalEntityModeChoiceUI,
                  gitlab_server_ui: GitlabServerNameUI,
                 active_ui: AbstractModalTrueFalseDefaultQuestionUI):
        super().__init__(feedback_ui)
        self._legal_entity_mode_ui = legal_entity_mode_ui
        self._gitlab_server_ui = gitlab_server_ui
        self._active_ui = active_ui

    async def CreateUpdateRoutine(self, name: str):
        fqdn = name
        user = get_local_user_routines()
        man = LegalEntityConfigManager(user)
        all = man.GetAll()
        config = None
        for item in all:
            if item.get_fqdn().lower() == fqdn.lower():
                config = item
        if config == None:
            config = man.FromParameters(fqdn, True, LegalEntityMode.NONE, "gitlab." + fqdn)

        # we have a config to update now.

        await self.get_feedback_ui().output("configuring fqdn: " + fqdn)
        legal_entity_mode = await self._legal_entity_mode_ui.execute("Legal Entity mode?")
        config.set_mode(legal_entity_mode)

        gitlab_server = await self._gitlab_server_ui.execute("Gitlab server name?", config.get_gitlab_server())
        config.set_gitlab_server(gitlab_server)

        active = await self._active_ui.execute("Active?", default=config.IsActive())
        config.set_active(active)

        await self.get_feedback_ui().output("Saving configuration.")

        # set before we leave
        man.Set([config])


class AutoManagerRoutines(object):
    """The AutoManager, called via main_routine walks through the Legal Entities and Containers that opt into being
    automanaged and that are configured appropriately.

    It resolves the correct GitLab server to use, and walks through any roots, pushing and pulling them
    appropriately.

    It will skip over any conflicts and warn about them.

    Once it has finished updating roots, it calls calls into AutoManager Structure plugins via the entrypoint named:

    fiepipe.plugin.automanager.automanage_structure

    with the call signature:

    call_name(feedback_ui:AbstractFeedbackUI, root_id:str, container_config:ContainerConfig, legal_entity_config:LegalEntityConfig, gitlab_server:str )

    Usually, it will continue doing this, sleeping between rounds, until it is asked to stop via 'request_close'.

    However, if 'once' is set to true when main_routine called, it will run once and return without sleeping.

    In this way, one can either use the simple, internal looping/sleeping logic, or their own, from the same simple call.
    """

    _sleep_length: float = 600.0
    _request_close = False

    def __init__(self, sleep_length: float):
        self._sleep_length = sleep_length

    def request_close(self):
        self._request_close = True

    async def main_routine(self, feedback_ui: AbstractFeedbackUI, once=False):
        self._request_close = False
        await feedback_ui.output("Starting AutoManager Main Routine...")
        while not self._request_close:
            # begin auto loop

            # first we loop through legal entities.

            registry = localregistry(get_local_user_routines())
            all_reg_entities = registry.GetAll()
            for reg_entity in all_reg_entities:
                fqdn = reg_entity.get_fqdn()

            #legal_entity_configs = self._get_active_legal_entitiy_configs()
            #for legal_entity_config in legal_entity_configs:

                # get the particualrs
                #mode = legal_entity_config.get_mode()

                # if the mode is none: we don't even bother.  this relieves others of checking further down the line.
                await self.automanage_fqdn(feedback_ui, fqdn)

            if once:
                self.request_close()
                break

            # wait for sleep length before running again
            await asyncio.sleep(self._sleep_length)

        # we've exited cleanly
        await feedback_ui.output("AutoManager Main Routine Complete.")
        return

    def get_legal_entitiy_config(self, fqdn: str) -> LegalEntityConfig:
        ret = []
        user = get_local_user_routines()
        man = LegalEntityConfigManager(user)
        all = man.GetAll()
        for item in all:
            if item.get_fqdn().lower() == fqdn.lower():
                return item
        raise KeyError()

    def get_container_config(self, local_container_config:LocalContainerConfiguration):
        return ContainerAutomanagerConfigurationComponent(local_container_config)



    async def automanage_fqdn(self, feedback_ui: AbstractFeedbackUI, fqdn:str):

        # pre automanage hook
        # we call regardless of mode.

        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.automanager.pre_automanage_fqdn")
        ret = {}
        for entrypoint in entrypoints:
            method = entrypoint.load()
            await method(feedback_ui, fqdn)

        # we get teh legal entity config after teh hook, becasue the pre_automanage hook might purposely alter
        # the config.  e.g. set a new gitlab server...

        try:
            legal_entity_config = self.get_legal_entitiy_config(fqdn)
        except KeyError as err:
            return

        if legal_entity_config.get_mode() == LegalEntityMode.NONE:
            return

        entity_registry = localregistry(get_local_user_routines())
        legal_entities = entity_registry.GetByFQDN(legal_entity_config.get_fqdn())
        if len(legal_entities) != 1:
            # return silently if the entity isn't currently registered.
            return

        legal_entity = legal_entities[0]

        await feedback_ui.output(
            "Found legal entity registration.  Beginning update: " + legal_entity_config.get_fqdn())


        gitlab_server = legal_entity_config.get_gitlab_server()

        await feedback_ui.output("Using GitLab Server: " + gitlab_server)

        gitlab_server_man = GitLabServerManager(get_local_user_routines())
        servers = gitlab_server_man.get_by_name(gitlab_server)

        if len(servers) == 0:
            await feedback_ui.error("GitLab Server not found: " + gitlab_server)
            return

        # Update Containers

        gitlab_server_routines = GitLabServerRoutines(gitlab_server)
        groupname = gitlab_server_routines.group_name_from_fqdn(legal_entity_config.get_fqdn())

        await feedback_ui.output("Updating and merging containers from GitLab FQDN group: " + groupname)

        container_management_routines = FQDNContainerManagementRoutines(feedback_ui, legal_entity_config.get_fqdn())
        gitlab_container_routines = GitlabManagedContainerRoutines(feedback_ui, container_management_routines,
                                                                   gitlab_server_routines)

        await gitlab_container_routines.safe_merge_update_routine(feedback_ui,groupname)

        await feedback_ui.output("Done updating and merging containers.")

        # next we go through the containers.
        user = get_local_user_routines()
        container_man = LocalContainerManager(user)
        #local_container_config_man = LocalContainerConfigurationManager(user)

        all_containers = container_man.GetByFQDN(legal_entity_config.get_fqdn())
        for container in all_containers:
            await self.automanage_container(feedback_ui, legal_entity_config, container.GetID(), gitlab_server)

    async def automanage_container(self, feedback_ui: AbstractFeedbackUI, legal_entity_config: LegalEntityConfig,
                                   container_id: str, gitlab_server: str):

        # pre automanage hook
        # we call regardless of mode.

        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.automanager.pre_automanage_container")
        ret = {}
        for entrypoint in entrypoints:
            method = entrypoint.load()
            await method(feedback_ui, legal_entity_config, container_id)

        # set up managers
        user = get_local_user_routines()
        container_man = LocalContainerManager(user)
        local_container_config_man = LocalContainerConfigurationManager(user)

        # we only execute those that exist, are locally configured and are active
        containers = container_man.GetByID(container_id)
        if len(containers) != 1:
            # we silently move on
            return

        container = containers[0]

        conatainer_local_configs = local_container_config_man.GetByID(container.GetID())
        if len(conatainer_local_configs) != 1:
            # we silently move on
            return

        container_local_config = conatainer_local_configs[0]

        config_component = ContainerAutomanagerConfigurationComponent(container_local_config)
        if not config_component.Exists():
            # we silently move on
            return

        config_component.Load()

        if not config_component.get_active():
            # we silently move on
            return

        await feedback_ui.output("Automanaging container: " + container.GetShortName())

        # resolve new gitlab server
        gitlab_server =  config_component.get_gitlab_server()

        await feedback_ui.output("Using GitLab Server: " + gitlab_server)

        gitlab_server_man = GitLabServerManager(get_local_user_routines())
        servers = gitlab_server_man.get_by_name(gitlab_server)

        if len(servers) == 0:
            await feedback_ui.error("GitLab Server not found: " + gitlab_server)
            return


        # root level auto management

        shared_roots_component = SharedGitRootsComponent(container)
        shared_roots_component.Load()
        shared_roots = shared_roots_component.GetItems()

        for shared_root in shared_roots:
            await self.automanage_root(feedback_ui, shared_root.GetID(), container_id, config_component,
                                       legal_entity_config,
                                       gitlab_server)

    async def automanage_root(self, feedback_ui: AbstractFeedbackUI, root_id: str, container_id: str,
                              container_config: ContainerAutomanagerConfigurationComponent,
                              legal_entity_config: LegalEntityConfig, gitlab_server: str):

        # pre automanage hook
        # we call regardless of mode.

        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.automanager.pre_automanage_root")
        ret = {}
        for entrypoint in entrypoints:
            method = entrypoint.load()
            await method(feedback_ui, legal_entity_config, container_config, root_id)


        # we only execute those that are configured and are checked out.

        root_routines = GitRootRoutines(container_id, root_id)
        root_routines.load()

        await feedback_ui.output("Automanaging root: " + root_routines.root.GetName())

        if not RepoExists(root_routines.get_local_repo_path()):
            await feedback_ui.output("Root not checked out.  Moving on.")
            return

        # update the root from gitlab.

        # TODO: per root gitlab server?

        # we update the root automatically in workstation mode.
        if legal_entity_config.get_mode() == LegalEntityMode.USER_WORKSTATION:
            gitlab_server_routines = GitLabServerRoutines(gitlab_server)
            gitlab_routines = GitLabFQDNGitRootRoutines(gitlab_server_routines, root_routines.root,
                                                        root_routines.root_config, legal_entity_config.get_fqdn())
            #does the remote exist.
            exists = await gitlab_routines.remote_exists(feedback_ui)

            if not exists:
                #we push it up if not
                await feedback_ui.output("Root doesn't exist on server.  Pushing...")
                success = await gitlab_routines.push_sub_routine(feedback_ui, 'master', False)
                if not success:
                    await feedback_ui.error("Failed to push new repository.  Aborting auto-management of this root")
                    return

            else:
                #if it exists, we check its ahead/behind status and act accordingly.
                is_behind_remote = await gitlab_routines.is_behind_remote(feedback_ui)
                is_ahead_of_remote = await gitlab_routines.is_aheadof_remote(feedback_ui)

                if is_ahead_of_remote and not is_behind_remote:
                    await feedback_ui.output("Root is ahead.  Pushing...")
                    success = await gitlab_routines.push_sub_routine(feedback_ui, 'master', False)
                    if not success:
                        await feedback_ui.warn(
                            "Failed to push commits.  This is not fatal.  Continuing auto-management of this root.")

                if is_ahead_of_remote and is_behind_remote:
                    await feedback_ui.output("Root is both ahead and behind. Pulling first...")
                    success = await gitlab_routines.pull_sub_routine(feedback_ui, 'master')
                    if not success:
                        await feedback_ui.error("Failed to pull from remote.  Aborting auto-management of this root.")
                        return
                    if not root_routines.is_in_conflict():
                        await feedback_ui.output("No conflicts found.  Pushing...")
                        success = await gitlab_routines.push_sub_routine(feedback_ui, 'master', False)
                        if not success:
                            await feedback_ui.warn(
                                "Failed to push commits.  This is not fatal.  Continuing auto-management of this root.")

                if not is_ahead_of_remote and is_behind_remote:
                    await feedback_ui.output("Root is behind.  Pulling...")
                    success = await gitlab_routines.pull_sub_routine(feedback_ui, 'master')
                    if not success:
                        await feedback_ui.warn("Failed to pull from remote.  Aborting auto-management of this root.")
                        return

                if root_routines.is_in_conflict():
                    await feedback_ui.warn(
                        "Root is in conflict.  You'll need to resolve this.  Aborting auto-management of this root.")
                    return

            # If we got here, the remote exists, we're not in conflict, and not knowingly behind.
            # The worktree might be dirty though.
            # However, auto adds and commits require some knowledge of structure.  So we leave a dirty root to be handled
            # by structure code for now.

        # from here, we need to automanage root structures.
        # structures are plugins.
        # every plugin structure type gets an opportunity to run here.  Each plugin is responsible
        # for determining if it should just do nothing and return, or if it needs to do something to
        # for this root.  As a rule, structures are supposed to be opt-in.

        entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.automanager.automanage_structure")
        ret = {}
        for entrypoint in entrypoints:
            method = entrypoint.load()
            await method(feedback_ui, root_id, container_id, container_config, legal_entity_config, gitlab_server)




class AutoManagerInteractiveRoutines(AutoManagerRoutines):

    def get_fqdns(self) -> typing.List[str]:
        ret = []
        registry = localregistry(get_local_user_routines())
        all = registry.GetAll()
        for item in all:
            ret.append(item.get_fqdn())
        return ret
