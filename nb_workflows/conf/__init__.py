import importlib
import os

from .types import Settings

# from logging import NullHandler


GLOBAL_MODULE = "nb_workflows.conf.global_settings"
ENVIRONMENT_VARIABLE = "NB_SETTINGS_MODULE"
DEFAULT_MODULE = os.environ.get(
    ENVIRONMENT_VARIABLE, "nb_app.settings")


def load(settings_module=DEFAULT_MODULE) -> Settings:
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

    cfg = Settings(**settings_dict)
    cfg.SETTINGS_MODULE = settings_module
    return cfg


# logging.basicConfig(format="%(asctime)s %(message)s")
# logging.getLogger(__name__).addHandler(NullHandler())
settings = load()
