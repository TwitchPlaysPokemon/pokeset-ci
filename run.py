"""
Runs the pokeset ci server.
"""
import os

import yaml

from pokesetci import PokesetCi, Config

BASE_PATH = os.path.dirname(__file__)


def load_config() -> Config:
    config = {}
    with open("config_default.yml") as default_config_file:
        default_config = yaml.load(default_config_file)
        config.update(default_config)
    with open("config.yml") as override_config_file:
        override_config = yaml.load(override_config_file)
        config.update(override_config)
    return Config(**config)


pokeset_ci = PokesetCi(config=load_config())
pokeset_ci.run()
