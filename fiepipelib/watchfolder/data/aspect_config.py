import typing

from fiepipelib.assetaspect.data.config import AspectConfiguration


class WatchFolderConfig(AspectConfiguration):

    def get_lfs_patterns(self) -> typing.List[str]:
        return []

    def get_git_ignores(self) -> typing.List[str]:
        return []

    def get_config_name(self) -> str:
        return "watch_folder"

    def from_json_data(self, data: typing.Dict):
        pass

    def to_json_data(self) -> typing.Dict:
        ret = {}
        return ret
