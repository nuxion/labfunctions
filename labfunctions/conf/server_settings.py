import importlib
import os

from labfunctions.types import ServerSettings

from . import load_server

# singleton pattern
# https://github.com/samuelcolvin/pydantic/issues/586
settings = load_server()
