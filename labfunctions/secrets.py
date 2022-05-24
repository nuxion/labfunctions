import logging
import os
from pathlib import Path
from typing import Any, Dict

from cryptography.fernet import Fernet

from labfunctions import defaults
from labfunctions.utils import Singleton

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
        logger.warning(f"No {vars_file} found")
        return {}


def load(base_path=None) -> Dict[str, Any]:

    priv_key = os.getenv(defaults.PRIVKEY_VAR_NAME)
    # base_path = define_base_path()
    if not priv_key:
        _file = os.getenv(defaults.NBVARS_VAR_NAME, f"local.nbvars")
        if base_path:
            _file = f"{base_path}/{_file}"
            _nbvars = _open_vars_file(vars_file=_file)
    else:
        f = Fernet(priv_key)
        _file = defaults.SECRETS_FILENAME
        if base_path:
            _file = f"{base_path}/{_file}"
        _vars = _open_vars_file(vars_file=_file)
        _nbvars = {k: f.decrypt(v.encode("utf-8")) for k, v in _vars.items()}
    return _nbvars


def generate_private_key() -> str:
    key = Fernet.generate_key()
    return key.decode("utf-8")


def decrypt(key: bytes, text: str) -> str:
    f = Fernet(key)
    return f.decrypt(text.encode("utf-8")).decode("utf-8")


def encrypt_nbvars_file(private_key: str, vars_file) -> Dict[str, Any]:
    """Open the file and encrypt it"""
    _vars = _open_vars_file(vars_file)
    f = Fernet(private_key)
    _nbvars = {
        k: f.encrypt(v.encode("utf-8")).decode("utf-8") for k, v in _vars.items()
    }
    return _nbvars


def encrypt_nbvars(private_key: str, nbvars_dict) -> Dict[str, Any]:
    """Expect the variables loaded from nbvars file"""
    f = Fernet(private_key)
    _nbvars = {
        k: f.encrypt(v.encode("utf-8")).decode("utf-8") for k, v in nbvars_dict.items()
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
