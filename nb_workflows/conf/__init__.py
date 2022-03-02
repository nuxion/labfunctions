import importlib
import os
import sys
from typing import Union

from .types import ClientSettings, ServerSettings

# from logging import NullHandler


GLOBAL_MODULE = "nb_workflows.conf.global_settings"
GLOBAL_CLIENT = "nb_workflows.conf.global_client"
ENVIRONMENT_VARIABLE = "NB_SETTINGS_MODULE"
CLIENT_VARIABLE = "NB_CLIENT_MODULE"
DEFAULT_MODULE = os.environ.get(
    ENVIRONMENT_VARIABLE, GLOBAL_MODULE)

DEFAULT_CLIENT = os.environ.get(CLIENT_VARIABLE, "nb_app.settings")


def load_server(settings_module=DEFAULT_MODULE) -> ServerSettings:
    try:
        mod = importlib.import_module(settings_module)
    except ModuleNotFoundError:
        mod = importlib.import_module(GLOBAL_MODULE)
    settings_dict = {}
    for m in dir(mod):
        if m.isupper():
            # sets.add(m)
            value = getattr(mod, m)
            settings_dict[m] = value

    cfg = ServerSettings(**settings_dict)
    cfg.SETTINGS_MODULE = settings_module
    return cfg


def load_client(settings_module=DEFAULT_CLIENT) -> ClientSettings:
    sys.path.append(os.getcwd())
    try:
        mod = importlib.import_module(settings_module)
    except ModuleNotFoundError:
        mod = importlib.import_module(GLOBAL_CLIENT)

    settings_dict = {}
    for m in dir(mod):
        if m.isupper():
            # sets.add(m)
            value = getattr(mod, m)
            settings_dict[m] = value

    cfg = ClientSettings(**settings_dict)
    cfg.SETTINGS_MODULE = settings_module
    return cfg


def load() -> \
        Union[ClientSettings, ServerSettings]:
    if os.environ.get("NB_SERVER", False):
        return load_server()
    else:
        return load_client()


settings = load_server()

settings_client = load_client()
