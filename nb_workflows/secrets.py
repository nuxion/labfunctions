import logging
import os
from typing import Any, Dict

from cryptography.fernet import Fernet

from nb_workflows.conf import defaults

logger = logging.getLogger(__name__)


def _parse_var_line(line):
    """
    This regex works only if spaces are not used
     ^(\w*)=?*(['|"].*?['|"|])$
    """
    k = line.split("=", maxsplit=1)[0]
    v = line.split("=", maxsplit=1)[1].replace('"', "").strip("\n")
    return k, v


def _open_vars_file(vars_file) -> Dict[str, Any]:
    """TODO: check regex:
    Vars are cleaned from spaces, return characters and quotes
    """
    try:
        with open(vars_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            vars_ = {}
            for line in lines:
                k, v = _parse_var_line(line)
                vars_.update({k: v})

            return vars_
    except FileNotFoundError:
        logger.warning(f"Not {vars_file} found")
        return {}


def load() -> Dict[str, Any]:

    priv_key = os.getenv(defaults.PRIVKEY_VAR_NAME)

    if not priv_key:
        _file = os.getenv(defaults.NBVARS_VAR_NAME, "local.nbvars")
        _nbvars = _open_vars_file(vars_file=_file)
    else:
        f = Fernet(priv_key)
        _vars = _open_vars_file(vars_file=defaults.SECRETS_FILENAME)
        _nbvars = {k: f.decrypt(v.encode("utf-8")) for k, v in _vars.items()}
    return _nbvars


def generate_private_key() -> str:
    key = Fernet.generate_key()
    return key.decode("utf-8")


def decrypt(key: bytes, text: str) -> str:
    f = Fernet(key)
    return f.decrypt(text.encode("utf-8")).decode("utf-8")


def encrypt_nbvars(private_key: str, vars_file) -> Dict[str, Any]:
    _vars = _open_vars_file(vars_file)
    f = Fernet(private_key)
    _nbvars = {
        k: f.encrypt(v.encode("utf-8")).decode("utf-8") for k, v in _vars.items()
    }
    return _nbvars


def write_secrets(fpath, private_key, vars_file) -> str:
    _vars = encrypt_nbvars(private_key, vars_file)
    newline = "\n"
    encoded_vars = f'{newline.join(f"{key}={value}" for key, value in _vars.items())}'
    outfile = f"{fpath}/{defaults.SECRETS_FILENAME}"
    with open(outfile, "w") as f:
        f.write(encoded_vars)

    return outfile


nbvars = load()
