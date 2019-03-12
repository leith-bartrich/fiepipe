import typing

from fiepipelib.gitaspect.routines.config import GitAspectConfigurationRoutines
from fiepipelib.rootaspect.data.config import RootAsepctConfiguration

TR = typing.TypeVar("TR", bound=RootAsepctConfiguration)


class RootAspectConfigurationRoutines(GitAspectConfigurationRoutines[TR], typing.Generic[TR]):
    pass