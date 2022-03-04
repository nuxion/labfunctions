import getpass
import json
from datetime import datetime
from pathlib import Path
from typing import Union

import httpx
import jwt

from nb_workflows.core.entities import NBTask, ScheduleData

from .types import Credentials


def _example_task() -> NBTask:
    t = NBTask(
        nb_name="test_workflow",
        alias="notebook.example",
        description="An example of how to configure a specific workflow",
        params=dict(TIMEOUT=5),
        schedule=ScheduleData(
            repeat=1,
            interval=10,
        ),
    )
    return t


def store_credentials(creds: Credentials, relative_path=".nb_workflows/"):
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    with open(f"{home}/{relative_path}/credentials.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(creds.dict()))


def get_credentials(relative_path=".nb_workflows/") -> Union[Credentials, None]:
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    try:
        with open(
            f"{home}/{relative_path}/credentials.json", "r", encoding="utf-8"
        ) as f:
            data = f.read()
            data_dict = json.loads(data)

            return Credentials(**data_dict)
    except FileNotFoundError:
        return None


def login_cli(with_server: str) -> Union[Credentials, None]:
    print(f"Your are connecting to {with_server}")
    u = input("User: ")
    p = getpass.getpass()
    rsp = httpx.post(f"{with_server}/auth", json=dict(username=u, password=p))
    try:
        creds = Credentials(**rsp.json())
        store_credentials(creds)
        return creds
    except KeyError:
        return None
    except TypeError:
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
