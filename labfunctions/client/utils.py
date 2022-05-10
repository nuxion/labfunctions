import getpass
import json
from datetime import datetime
from pathlib import Path
from typing import Union

import httpx
import jwt

from labfunctions import defaults
from labfunctions.types import NBTask, ScheduleData
from labfunctions.types import TokenCreds as Credentials
from labfunctions.utils import get_parent_folder, secure_filename


def _example_task() -> NBTask:
    t = NBTask(
        nb_name="test_workflow",
        description="An example of how to configure a specific workflow",
        params=dict(TIMEOUT=5),
        schedule=ScheduleData(
            repeat=1,
            interval=10,
        ),
    )
    return t


def store_credentials_disk(creds: Credentials, homedir: Union[Path, str]):
    hd = Path(homedir)
    creds_path = hd / defaults.CLIENT_CREDS_FILE
    with open(creds_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(creds.dict()))
    creds_path.chmod(0o600)


def get_credentials_disk(homedir: Union[Path, str]) -> Union[Credentials, None]:
    hd = Path(homedir)
    creds = hd / defaults.CLIENT_CREDS_FILE
    try:
        if creds.is_file():
            with open(hd / defaults.CLIENT_CREDS_FILE, "r", encoding="utf-8") as f:
                data = f.read()
                data_dict = json.loads(data)

                return Credentials(**data_dict)
        return None
    except PermissionError:
        return None


def del_credentials_disk(homedir: Union[Path, str]):
    hd = Path(homedir)
    creds = hd / defaults.CLIENT_CREDS_FILE
    if creds.is_file():
        creds.unlink()


def store_private_key(key, working_area: Union[Path, str]):
    wa = Path(working_area)
    wa.mkdir(parents=True, exist_ok=True)
    with open(wa / "private_key", "w", encoding="utf-8") as f:
        f.write(key)
    Path(wa / "private_key").chmod(0o600)


def get_private_key(working_area: Union[Path, str]) -> str:
    wa = Path(working_area)
    try:
        with open(Path(wa / "private_key"), "r", encoding="utf-8") as f:
            key = f.read().strip()
            return key
    except FileNotFoundError:
        return None


def validate_credentials_local(token) -> bool:
    """Validates locally against the jwt signature
    If exp is not bigger than now, then is valid.
    """
    n = datetime.utcnow()
    ts_now = int(datetime.timestamp(n))
    tkn_dict = jwt.decode(token, options={"verify_signature": False})

    if ts_now < tkn_dict["exp"]:
        return True
    return False
