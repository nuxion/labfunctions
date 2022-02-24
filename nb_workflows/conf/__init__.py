import importlib
import logging
import os
from logging import NullHandler

from .types import Settings

ENVIRONMENT_VARIABLE = "NB_SETTINGS_MODULE"
DEFAULT_MODULE = os.environ.get(
    ENVIRONMENT_VARIABLE, "nb_workflows.conf.global_settings")


def load(settings_module=DEFAULT_MODULE) -> Settings:
    mod = importlib.import_module(settings_module)
    settings_dict = {}
    for m in dir(mod):
        if m.isupper():
            # sets.add(m)
            value = getattr(mod, m)
            settings_dict[m] = value

    cfg = Settings(**settings_dict)
    cfg.SETTINGS_MODULE = settings_module
    return cfg


# logging.basicConfig(format="%(asctime)s %(message)s")
# logging.getLogger(__name__).addHandler(NullHandler())
settings = load()
