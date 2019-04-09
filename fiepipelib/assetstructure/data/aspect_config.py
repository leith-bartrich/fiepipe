import typing
import abc

from fiepipelib.gitaspect.data.config import GitAspectConfiguration
from fiepipelib.rootaspect.data.config import RootAsepctConfiguration
from fiepipelib.assetaspect.data.config import AssetAspectConfiguration


class GitDesktopStructureAspectConfiguration(GitAspectConfiguration, abc.ABC):
    """An aspect configuration meant to confgiure a Desktop Git Structure."""



class RootDesktopStructureAspectConfiguration(RootAsepctConfiguration, GitDesktopStructureAspectConfiguration, abc.ABC):
    """An aspect configuration meant to configure a Deskop Root Structure."""
    pass


class AssetDesktopStructureAspectConfiguration(AssetAspectConfiguration, GitDesktopStructureAspectConfiguration, abc.ABC):
    """An aspect configuration meant to configure a Desktop Asset Structure"""
    pass

