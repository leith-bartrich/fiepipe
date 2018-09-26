import os
import pathlib
import textwrap
import typing

from fiepipelib.localuser.routines.localuser import LocalUserRoutines
from fiepipelib.storage.localvolume import CommonAdjectivesDict, GetHomeVolume
from fiepipelib.storage.localvolume import localvolume, localvolumeregistry, GetAllMountedVolumes, FromParameters, \
    SetupUnregisteredRemovableVolume
from fiepipelib.storage.routines.ui.volumes import NewVolumeNameInputUI
from fieui.ChoiceInputModalUI import AbstractChoiceInputModalUI
from fieui.FeedbackUI import AbstractFeedbackUI


class LocalStorageRoutines(object):
    _localUser: LocalUserRoutines = None
    _feedbackUI: AbstractFeedbackUI = None
    _choiceUI: AbstractChoiceInputModalUI[str] = None
    _new_volume_name_ui: NewVolumeNameInputUI = None

    def __init__(self, localUser: LocalUserRoutines, feedbackUI: AbstractFeedbackUI,
                 choiceUI: AbstractChoiceInputModalUI[str], new_volume_name_ui: NewVolumeNameInputUI):
        self._localUser = localUser
        self._feedbackUI = feedbackUI
        self._choiceUI = choiceUI
        self._new_volume_name_ui = new_volume_name_ui

    def get_home_volume(self) -> localvolume:
        return GetHomeVolume(self._localUser)

    def get_all_mounted_volumes(self) -> typing.List[localvolume]:
        """Gets all local volumes that are currenlty mounted."""
        return GetAllMountedVolumes(self._localUser)

    def get_configured_volumes(self) -> typing.List[localvolume]:
        """Gets all local volumes that have been configured in the manager."""
        man = localvolumeregistry(self._localUser)
        return man.GetAll()

    async def delete_configured_volume_routine(self, name: str):
        """Deletes the named configured storage.
        arg name: the name of the configured storage to delete"""
        man = localvolumeregistry(self._localUser)
        man.DeleteByName(name)

    async def create_volume_routine(self, name: str, path: str):
        """Creates a named configured volume.
        arg name: the name of the new volume.  No spaces please.
        arg path: the absolute path of the new storage volume.  Spaces are allowed but always discouraged.
        """
        if not os.path.isabs(path):
            await self._feedbackUI.error("Path must be absolute: " + path)
            raise IOError("Not absolute: " + path)
        vol = FromParameters(name, path)
        manager = localvolumeregistry(self._localUser)
        manager.Set([vol])

    def get_available_adjectives(self) -> typing.Dict[str, typing.Dict[str, str]]:
        """Gets a categorized list of the 'known' or 'available adjectives in the current context,and descriptions."""
        return CommonAdjectivesDict()

    async def print_adjectives_routine(self):
        adjectives = self.get_available_adjectives()
        await self._feedbackUI.output("Available Adjectives:")
        for catName in adjectives.keys():
            await self._feedbackUI.output("  " + catName + ":")
            cat = adjectives[catName]
            for adj in cat.keys():
                await self._feedbackUI.output("    " + adj + ":")
                await self._feedbackUI.output(textwrap.indent(textwrap.fill(cat[adj]), "      "))

    def add_adjective(self, volume: localvolume, adj: str):
        manager = localvolumeregistry(self._localUser)

        if not volume.HasAdjective(adj):
            volume.AddAdjective(adj)
            manager.Set([volume])

    async def add_adjective_routine(self, volume: localvolume):

        manager = localvolumeregistry(self._localUser)
        adjectives = self.get_available_adjectives()
        choices = {}
        for catName in adjectives.keys():
            cat = adjectives[catName]
            for adj in cat.keys():
                desc = cat[adj]
                choice = catName + ":" + adj
                choices[choice] = adj

        to_add = await self._choiceUI.execute("Adjective to add?", choices)

        self.add_adjective(volume, to_add[1])

    def do_delete_adjective(self, volume: localvolume, adj: str):
        manager = localvolumeregistry(self._localUser)
        if volume.HasAdjective(adj):
            volume.RemoveAdjective(adj)
            manager.Set([volume])

    async def do_delete_adjective_routine(self, volume: localvolume):
        choices = dict()
        for adj in volume.GetAdjectives():
            choices[adj] = adj
        choice, to_remove = await self._choiceUI.execute("Adjective to remove?", choices)
        self.do_delete_adjective(volume,to_remove)

    async def do_setup_removable(self, path: str):

        pth = pathlib.Path(path)

        if not pth.is_dir():
            await self._feedbackUI.error("Not a valid path to a directory.")
            return

        named = False
        name = ""

        while not named:
            name = await self._stringInputUI.execute("Name for removable volume")
            if name == "":
                await  self._feedbackUI.warn("Volume must be given a name.")
            else:
                named = True

        SetupUnregisteredRemovableVolume(str(pth.absolute()), name)
