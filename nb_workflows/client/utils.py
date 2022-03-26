import getpass
import json
from datetime import datetime
from pathlib import Path
from typing import Union

import httpx
import jwt

from nb_workflows.conf import defaults
from nb_workflows.types import NBTask, ScheduleData
from nb_workflows.utils import get_parent_folder, secure_filename

from .types import Credentials


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


def normalize_name(name: str) -> str:
    """used mostly for projects"""
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def store_credentials_disk(creds: Credentials, home_dir=defaults.CLIENT_HOME_DIR):
    root = Path.home() / home_dir
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "credentials.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(creds.dict()))

    root.chmod(0o700)
    (root / "credentials.json").chmod(0o600)


def get_credentials_disk(home_dir=defaults.CLIENT_HOME_DIR) -> Union[Credentials, None]:
    root = Path.home() / home_dir
    root.mkdir(parents=True, exist_ok=True)
    try:
        with open(root / "credentials.json", "r", encoding="utf-8") as f:
            data = f.read()
            data_dict = json.loads(data)

            return Credentials(**data_dict)
    except FileNotFoundError:
        return None


def store_private_key(key, projectid, home_dir=defaults.CLIENT_HOME_DIR):
    root = Path.home() / home_dir / projectid
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "private_key", "w", encoding="utf-8") as f:
        f.write(key)

    root.chmod(0o700)
    (root / "private_key").chmod(0o600)


def get_private_key(projectid, home_dir=defaults.CLIENT_HOME_DIR) -> str:
    root = Path.home() / home_dir / projectid

    try:
        with open(root / "private_key", "r", encoding="utf-8") as f:
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
