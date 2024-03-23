import json
import os
from typing import List


class JsonLoadable():
    def assign_from_json(self, json_dict: dict):
        # Iter all keys in the json dict
        for key in json_dict:
            if hasattr(self, key):
                if isinstance(getattr(self, key), JsonLoadable):
                    getattr(self, key).assign_from_json(json_dict[key])
                else:
                    setattr(self, key, json_dict[key])


class Examples(JsonLoadable):
    def __init__(self):
        self.order: List[str] = []
        self.ignoreUnlisted = False
        self.ignore: List[str] = []
        # self.createReadme = True


class ExamplesConfig(JsonLoadable):
    def __init__(self):
        self.header: str = None
        self.info: str = None
        self.examples = Examples()

    @staticmethod
    def from_file(config_file: str):
        c = ExamplesConfig()
        if os.path.isfile(config_file):
            with open(config_file, "r") as f:
                mdplus_json = json.loads(f.read())
                c.assign_from_json(mdplus_json)

        return c
