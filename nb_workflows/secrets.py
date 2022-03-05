import logging
import os
from typing import Any, Dict

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def _open_vars_file(vars_file) -> Dict[str, Any]:
    try:
        with open(vars_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

            vars_ = {l.split()[0]: l.split()[1] for l in lines}
            return vars_
    except FileNotFoundError:
        logger.warning(f"Not {vars_file} found")
        return {}


def load() -> Dict[str, Any]:

    if not os.getenv("PRIVATE_KEY"):
        _file = os.getenv("NBVARS", "local.nbvars")
        _nbvars = _open_vars_file(vars_file=_file)
    else:
        f = Fernet(os.getenv("PRIVATE_KEY"))
        _vars = _open_vars_file(vars_file=".secrets")
        _nbvars = {k: f.decrypt(v) for k, v in _vars.items()}
    return _nbvars


nbvars = load()
