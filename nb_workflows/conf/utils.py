import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path

from . import defaults
from .types import ClientSettings, ServerSettings

# from nb_workflows.utils import define_base_path


# from logging import NullHandler


# Server defaults
GLOBAL_MODULE = "nb_workflows.conf.global_settings"
ENVIRONMENT_VARIABLE = "NB_SETTINGS_MODULE"
DEFAULT_MODULE = os.environ.get(ENVIRONMENT_VARIABLE, GLOBAL_MODULE)

# Client defaults
GLOBAL_CLIENT = "nb_workflows.conf.global_client"
CLIENT_VARIABLE = "NB_CLIENT_MODULE"
DEFAULT_CLIENT_MOD = os.environ.get(CLIENT_VARIABLE, "nb_app.settings")


def _get_level(level):
    return getattr(logging, level)


def execute_cmd(cmd) -> str:
    """Wrapper around subprocess"""
    with subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as p:

        out, err = p.communicate()
        if err:
            raise AttributeError(err.decode())

        return out.decode().strip()


def define_base_path() -> str:
    """
    It tries to determine a base path for BASE_PATH in settings.
    If a environment var exist for this, then it will use that, else
    it will use git, if fail it will go to an upper level.

    """
    root_dir = os.getcwd()
    base_path = root_dir

    base_var = os.environ.get(defaults.BASE_PATH_ENV)
    # is_interactive = _is_interactive_shell()
    if not base_var:
        try:
            base_path = execute_cmd("git rev-parse --show-toplevel")
        except:
            base_path = str(Path(root_dir).parents[0])
    elif base_var:
        base_path = base_var

    return base_path


def load_client(settings_module=DEFAULT_CLIENT_MOD) -> ClientSettings:
    # sys.path.append(os.getcwd())
    module_loaded = settings_module
    base_path = define_base_path()

    if not os.environ.get(CLIENT_VARIABLE):
        sys.path.append(base_path)

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

    bp = settings_dict.get("BASE_PATH")
    if bp:
        base_path = bp
    else:
        settings_dict["BASE_PATH"] = base_path

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
