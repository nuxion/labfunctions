import importlib
import os

from . import load_server
from .types import ServerSettings

# singleton pattern
# https://github.com/samuelcolvin/pydantic/issues/586
settings = load_server()
