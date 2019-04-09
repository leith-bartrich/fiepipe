from fiepipelib.automanager.routines.automanager import GitlabServerNameUI
from fiepipelib.components.routines.component import AbstractComponentRoutines
from fiepipelib.container.local_config.data.automanager import ContainerAutomanagerConfigurationComponent
from fieui.FeedbackUI import AbstractFeedbackUI
from fieui.ModalTrueFalseDefaultQuestionUI import AbstractModalTrueFalseDefaultQuestionUI


class ContainerAutomanagerConfigurationComponentRoutines(
    AbstractComponentRoutines[ContainerAutomanagerConfigurationComponent]):

    def new_component(self) -> ContainerAutomanagerConfigurationComponent:
        ret = ContainerAutomanagerConfigurationComponent(self.get_container_routines().get_container())
        return ret

    async def print_routine(self, feedback_ui: AbstractFeedbackUI):
        self.get_container_routines().load()
        self.load()
        comp = self.get_component()
        await feedback_ui.output("active: " + str(comp.get_active()))
        await feedback_ui.output("gitlab_server: " + str(comp.get_gitlab_server()))

        await feedback_ui.output("root gitlab_server overrides:")
        for root_id in comp.get_root_gitlab_server_overrides().keys():
            servername = comp.get_root_gitlab_server_overrides()[root_id]
            await feedback_ui.output("  " + root_id + " : " + servername)

        await feedback_ui.output("asset gitlab_server overrides:")
        for asset_id in comp.get_asset_gitlab_server_overrides().keys():
            servername = comp.get_asset_gitlab_server_overrides()[asset_id]
            await feedback_ui.output("  " + asset_id + " : " + servername)


class ContainerAutomanagerConfigurationComponentRoutinesInteractive(ContainerAutomanagerConfigurationComponentRoutines):

    async def reconfigure_routine(self, feedback_ui: AbstractFeedbackUI,
                                  active_ui: AbstractModalTrueFalseDefaultQuestionUI,
                                  gitlab_server_name_ui: GitlabServerNameUI):
        self.get_container_routines().load()
        self.load()
        comp = self.get_component()
        gitlab_server = await gitlab_server_name_ui.execute("Gitlab server name?", comp.get_gitlab_server())
        active = await active_ui.execute("Active?", default=comp.get_active())
        comp.set_gitlab_server(gitlab_server)
        comp.set_active(active)
        self.commit()
        self.get_container_routines().commit()
