import importlib
import os
import sys

from . import load_client
from .types import ClientSettings

GLOBAL_CLIENT = "nb_workflows.conf.global_client"
CLIENT_VARIABLE = "NB_CLIENT_MODULE"
DEFAULT_CLIENT = os.environ.get(CLIENT_VARIABLE, "nb_app.settings")

# singleton pattern
# https://github.com/samuelcolvin/pydantic/issues/586
settings = load_client()
