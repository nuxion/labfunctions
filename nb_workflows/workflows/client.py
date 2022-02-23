import getpass
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx
import toml
from nb_workflows.conf import Config
from nb_workflows.workflows.entities import NBTask, ScheduleData


def _open_toml(filepath: str):
    with open(filepath, "r") as f:
        tf = f.read()

    tomconf = toml.loads(tf)
    return tomconf


@dataclass
class NBCliConfig:
    url_service: str
    version: str
    workflows: List[NBTask]
    # workflows: Dict[str, NBTask]


@dataclass
class WFCreateRsp:
    status_code: int
    msg: Optional[str] = None
    jobid: Optional[str] = None


@dataclass
class ScheduleExecRsp:
    status_code: int
    msg: Optional[str] = None
    executionid: Optional[str] = None


@dataclass
class ScheduleListRsp:
    nb_name: str
    jobid: str
    enabled: bool
    description: Optional[str] = None


def validate_credentials(websrv, token) -> bool:
    _headers = {"Authorization": f"Bearer {token}"}

    r = httpx.get(f"{websrv}/auth/verify",
                  headers=_headers)
    if r.status_code == 200:
        return True
    if r.status_code == 401:
        return False
    raise TypeError("Wrong communitacion against {websrv}")


class NBClient:
    """NB Workflow client"""

    def __init__(self, token: str, conf: NBCliConfig):
        self._data = conf
        self._workflows = conf.workflows
        self._addr = conf.url_service
        self._headers = {"Authorization": f"Bearer {token}"}

    def write(self, output="workflows.toml"):
        with open(output, "w", encoding="utf-8") as f:
            _dump = toml.dumps(asdict(self._data))
            f.write(_dump)

    def create_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.post(f"{self._addr}/workflows/schedule",
                       json=asdict(t),
                       headers=self._headers)

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def push_all(self, refresh_workflows=True):
        for task in self._workflows:
            r = self.create_workflow(task)
            if r.status_code == 200:
                print(f"Workflow {task.schedule['alias']} already exist")
            elif r.status_code == 201:
                print(
                    f"Workflow {task.schedule['alias']} created. Jobid: {r.jobid}"
                )
                if refresh_workflows:
                    task.jobid = r.jobid
            elif r.status_code == 401:
                print(
                    "Auth failed"
                )

        if refresh_workflows:
            self.write()

    def list_scheduled(self) -> List[ScheduleListRsp]:
        r = httpx.get(f"{self._addr}/workflows/schedule",
                      headers=self._headers)
        data = [
            ScheduleListRsp(
                nb_name=s["nb_name"],
                jobid=s["jobid"],
                enabled=s["enabled"],
                description=s.get("description"),
            )
            for s in r.json()
        ]
        return data

    def execute_remote(self, jobid) -> ScheduleExecRsp:
        r = httpx.post(f"{self._addr}/workflows/schedule/{jobid}/_run",
                       headers=self._headers)
        return ScheduleExecRsp(r.status_code, executionid=r.json()["executionid"])

    def delete(self, jobid) -> int:
        r = httpx.delete(f"{self._addr}/workflows/schedule/{jobid}",
                         headers=self._headers)
        return r.status_code


def init(url_service, version="0.1.0") -> NBClient:
    t = NBTask(
        nb_name="test_workflow",
        description="An example of how to configure a specific workflow",
        params=dict(TIMEOUT=5),
        schedule=ScheduleData(
            alias="notebook.example",
            repeat=1,
            interval=10,
        ),
    )
    nbc = NBCliConfig(version=version, url_service=url_service, workflows=[t])

    return NBClient(token="", conf=nbc)


def open_config(filepath) -> NBCliConfig:
    data_dict = _open_toml(filepath)
    nbc = NBCliConfig(**data_dict)
    return nbc


def from_file(filepath, token) -> NBClient:
    nbc = open_config(filepath)
    nbc.workflows = [NBTask(**w) for w in nbc.workflows]
    obj = NBClient(token, nbc)

    return obj


def from_remote(url_service, token, version="0.1.0") -> NBClient:
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{url_service}/workflows/schedule", headers=headers)
    workflows = []
    for w_data in r.json():
        obj = NBTask(**w_data["job_detail"])
        obj.jobid = w_data["jobid"]
        workflows.append(obj)
    nbc = NBCliConfig(url_service, version, workflows=workflows)
    return NBClient(token, nbc)


def login_cli(with_server: str) -> Union[str, None]:
    u = input("User: ")
    p = getpass.getpass()
    rsp = httpx.post(f"{with_server}/auth", json=dict(username=u, password=p))
    try:
        tkn = rsp.json()["access_token"]
        store_credentials(tkn)
        return tkn
    except KeyError:
        return None


def store_credentials(token, relative_path=".nb_workflows/"):
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    with open(f"{home}/{relative_path}/credentials", "w", encoding="utf-8") as f:
        f.write(token)


def get_credentials(relative_path=".nb_workflows/") -> Union[str, None]:
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    try:
        with open(f"{home}/{relative_path}/credentials", "r", encoding="utf-8") as f:
            data = f.read()
            return data
    except FileNotFoundError:
        return None
