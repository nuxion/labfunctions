import importlib
import logging
import os
import sys

from nb_workflows.secrets2 import load

from .utils import load_client


def _get_level(level):
    return getattr(logging, level)


# singleton pattern
# https://github.com/samuelcolvin/pydantic/issues/586
settings = load_client()
