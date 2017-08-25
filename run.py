"""
Runs the pokeset ci server.
"""
import logging
import os
import sys
import time

import yaml

from pokesetci import PokesetCi, Config

BASE_PATH = os.path.dirname(__file__)

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d]\t[%(levelname)s]\t[%(name)s]\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


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
