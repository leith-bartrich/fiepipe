import abc
import json
import os.path
import pathlib
import typing
from abc import abstractmethod


class GitAspectConfiguration(abc.ABC):

    @abc.abstractmethod
    def get_config_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_worktree_path(self) -> str:
        pass

    def get_config_path(self) -> str:
        return os.path.join(self.get_config_dir_path(), self.get_config_name() + ".json")

    def get_config_dir_path(self) -> str:
        return os.path.join(self.get_worktree_path(), 'asset_configs')

    def exists(self) -> bool:
        path = pathlib.Path(self.get_config_path())
        return path.exists()

    @abc.abstractmethod
    def from_json_data(self, data: typing.Dict):
        """From the given data dictionary, populate this configuration."""
        raise NotImplementedError()

    def load(self):
        with open(self.get_config_path(), 'r') as f:
            data = json.load(f)
            self.from_json_data(data)

    def commit(self):
        if not os.path.exists(self.get_config_dir_path()):
            os.makedirs(self.get_config_dir_path())
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