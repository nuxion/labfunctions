import importlib
import logging
import os
import sys

from . import defaults
from .types import ClientSettings, ServerSettings

# from logging import NullHandler


# Client defaults
GLOBAL_CLIENT = "nb_workflows.conf.global_client"
CLIENT_VARIABLE = "NB_CLIENT_MODULE"
DEFAULT_CLIENT = os.environ.get(CLIENT_VARIABLE, "nb_app.settings")

# Server defaults
GLOBAL_MODULE = "nb_workflows.conf.global_settings"
ENVIRONMENT_VARIABLE = "NB_SETTINGS_MODULE"
DEFAULT_MODULE = os.environ.get(ENVIRONMENT_VARIABLE, GLOBAL_MODULE)


def _get_level(level):
    return getattr(logging, level)


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

    if not cfg.DEBUG:
        _level = _get_level(cfg.LOGLEVEL)
    else:
        _level = logging.DEBUG

    # set BASE_PATH
    os.environ[defaults.BASE_PATH_ENV] = cfg.BASE_PATH

    logging.basicConfig(format=cfg.LOGFORMAT, level=_level)

    return cfg


def load_client(settings_module=DEFAULT_CLIENT) -> ClientSettings:
    # sys.path.append(os.getcwd())
    module_loaded = settings_module
    try:
        mod = importlib.import_module(settings_module)
    except ModuleNotFoundError:
        mod = importlib.import_module(GLOBAL_CLIENT)
        module_loaded = GLOBAL_CLIENT

    settings_dict = {}
    for m in dir(mod):
        if m.isupper():
            # sets.add(m)
            value = getattr(mod, m)
            settings_dict[m] = value

    cfg = ClientSettings(**settings_dict)
    cfg.SETTINGS_MODULE = module_loaded
    if not cfg.DEBUG:
        _level = _get_level(cfg.LOGLEVEL)
    else:
        _level = logging.DEBUG

    # set BASE_PATH
    # os.environ[defaults.BASE_PATH_ENV] = cfg.BASE_PATH

    logging.basicConfig(format=cfg.LOGFORMAT, level=_level)
    log = logging.getLogger(__name__)
    log.debug("Using {cfg.SETTINGS_MODULE} as config module")

    return cfg
