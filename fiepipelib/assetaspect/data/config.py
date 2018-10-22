import abc
import json
import os.path
import pathlib
import typing


class AspectConfiguration(abc.ABC):

    @abc.abstractmethod
    def get_config_name(self) -> str:
        raise NotImplementedError()

    def get_config_path(self) -> str:
        return os.path.join(self._asset_path, 'asset_configs', self.get_config_name() + ".json")

    _asset_path: str = None

    def __init__(self, asset_path: str):
        self._asset_path = asset_path

    def exists(self) -> bool:
        path = pathlib.Path(self.get_config_path())
        return path.exists()

    def load(self):
        with open(self.get_config_path(), 'r') as f:
            data = json.load(f)
            self.from_json_data(data)

    @abc.abstractmethod
    def from_json_data(self, data: typing.Dict):
        """From the given data dictionary, populate this configuration."""
        raise NotImplementedError()

    def commit(self):
        with open(self.get_config_path(), 'w') as f:
            data = self.to_json_data()
            json.dump(data, f)
            f.flush()
            f.close()

    def delete(self):
        os.remove(self.get_config_path())

    @abc.abstractmethod
    def to_json_data(self) -> typing.Dict:
        """From this configuration, create a data dictionary and return it."""
        raise NotImplementedError()
