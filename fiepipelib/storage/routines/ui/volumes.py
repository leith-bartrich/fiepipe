import typing
from abc import ABC
from fiepipelib.storage.localvolume import GetAllRegisteredLocalVolumes, GetHomeVolume, localvolume
from fieui.InputModalUI import AbstractInputModalUI
from fiepipelib.localplatform.routines.localplatform import get_local_platform_routines
from fiepipelib.localuser.routines.localuser import LocalUserRoutines

class NewVolumeNameInputUI(AbstractInputModalUI[str], ABC):

    def validate(self, v: str) -> typing.Tuple[bool, str]:
        plat = get_local_platform_routines()
        user = LocalUserRoutines(plat)

        #check it doesn't already exist
        local_vols = GetAllRegisteredLocalVolumes(user)
        for local_vol in local_vols:
            if local_vol.GetName() == v:
                return False, v
        return True, v


def get_local_volume_choices(adjectives_filter: typing.List[str]):
    plat = get_local_platform_routines()
    user = LocalUserRoutines(plat)
    all_vols = GetAllRegisteredLocalVolumes(user)
    all_vols.append(GetHomeVolume(user))
    choices = {}
    for vol in all_vols:
        assert isinstance(vol, localvolume)
        should_add = False
        if len(adjectives_filter) == 0:
            should_add = True
        else:
            for adj in adjectives_filter:
                if vol.HasAdjective(adj):
                    should_add = True
        if should_add:
            choices[vol.GetName()] = vol
    return choices