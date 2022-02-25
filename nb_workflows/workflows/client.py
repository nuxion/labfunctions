import getpass
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx
import toml
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
    workflows: Optional[List[NBTask]] = None
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


@dataclass
class WorkflowRsp:
    enabled: bool
    task: NBTask


@dataclass
class CredentialsRsp:
    access_token: str
    refresh_token: Optional[str] = None


def validate_credentials(websrv, token) -> bool:
    _headers = {"Authorization": f"Bearer {token}"}

    r = httpx.get(f"{websrv}/auth/verify", headers=_headers)
    if r.status_code == 200:
        return True
    if r.status_code == 401:
        return False
    raise TypeError("Wrong communitacion against {websrv}")


class NBClient:
    """NB Workflow client"""

    def __init__(self, creds: CredentialsRsp, conf: NBCliConfig):
        self._data = conf
        self._workflows = conf.workflows
        self._addr = conf.url_service
        self.creds = creds
        self._headers = {"Authorization": f"Bearer {creds.access_token}"}

    def refresh(self):
        r = httpx.post(f"{self._addr}/auth/refresh",
                       json={"refresh_token": self.creds.refresh_token},
                       headers=self._headers)
        data = r.json()
        print(data)
        self.creds.access_token = data["access_token"]
        store_credentials(self.creds)

    def verify_or_refresh(self) -> bool:
        valid = validate_credentials(self._addr,
                                     self.creds.access_token)
        if not valid:
            self.refresh()
            return True
        return False

    def write(self, output="workflows.toml"):
        with open(output, "w", encoding="utf-8") as f:
            _dump = toml.dumps(asdict(self._data))
            f.write(_dump)

    def create_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.post(
            f"{self._addr}/workflows/schedule",
            json=asdict(t),
            headers=self._headers,
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def update_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.put(
            f"{self._addr}/workflows/schedule",
            json=asdict(t),
            headers=self._headers,
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def push_all(self, refresh_workflows=True, update=False):
        _workflows = []
        for task in self._workflows:
            if update:
                r = self.update_workflow(task)
            else:
                r = self.create_workflow(task)
            if r.status_code == 200:
                print(f"Workflow {task.alias} already exist")
            elif r.status_code == 201:
                print(f"Workflow {task.alias} created. Jobid: {r.jobid}")
                if refresh_workflows:
                    task.jobid = r.jobid
            elif r.status_code == 401:
                print("Auth failed")
            _workflows.append(task)

        if refresh_workflows:
            self._workflows = _workflows
            self.write()

    def list_scheduled(self) -> List[ScheduleListRsp]:
        self.verify_or_refresh()
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

    def get_workflow(self, jobid) -> Union[WorkflowRsp, None]:
        self.verify_or_refresh()
        r = httpx.get(f"{self._addr}/workflows/schedule/{jobid}",
                      headers=self._headers)
        if r.status_code == 200:
            data_dict = r.json()
            task = NBTask(**data_dict['job_detail'])
            task.jobid = jobid
            task.schedule = ScheduleData(**data_dict["job_detail"]["schedule"])

            return WorkflowRsp(task=task, enabled=data_dict["enabled"])
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def rq_cancel_job(self, jobid) -> int:
        r = httpx.delete(
            f"{self._addr}/workflows/schedule/rqjobs/_cancel/{jobid}",
            headers=self._headers
        )
        if r.status_code != 200:
            raise TypeError("Something went wrong with %s", jobid)
        return r.status_code

    def execute_remote(self, jobid) -> ScheduleExecRsp:
        self.verify_or_refresh()
        r = httpx.post(
            f"{self._addr}/workflows/schedule/{jobid}/_run",
            headers=self._headers
        )
        return ScheduleExecRsp(r.status_code, executionid=r.json()["executionid"])

    def delete(self, jobid) -> int:
        r = httpx.delete(
            f"{self._addr}/workflows/schedule/{jobid}", headers=self._headers
        )
        return r.status_code

    def history_last(self, jobid):
        r = httpx.get(
            f"{self._addr}/workflows/history/{jobid}", headers=self._headers
        )
        return r.json()

    def rq_status(self, jobid):
        r = httpx.get(
            f"{self._addr}/workflows/rqjobs/{jobid}", headers=self._headers
        )
        return r.json()


def _example() -> NBTask:
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


def init(url_service, example, from_remote=False, version="0.1.0") -> NBClient:
    task = None
    if example:
        task = [_example()]

    nbc = NBCliConfig(
        version=version, url_service=url_service, workflows=task)
    creds = login_cli(url_service)

    return NBClient(creds=creds, conf=nbc)


def open_config(filepath) -> NBCliConfig:
    data_dict = _open_toml(filepath)
    nbc = NBCliConfig(**data_dict)
    return nbc


def from_file(filepath) -> NBClient:
    nbc = open_config(filepath)
    if nbc.workflows:
        nbc.workflows = [NBTask(**w) for w in nbc.workflows]

    creds = get_credentials()

    obj = NBClient(creds, nbc)

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


def login_cli(with_server: str) -> Union[CredentialsRsp, None]:
    u = input("User: ")
    p = getpass.getpass()
    rsp = httpx.post(f"{with_server}/auth", json=dict(username=u, password=p))
    try:
        creds = CredentialsRsp(**rsp.json())
        store_credentials(creds)
        return creds
    except KeyError:
        return None
    except TypeError:
        return None


def store_credentials(creds: CredentialsRsp, relative_path=".nb_workflows/"):
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    with open(f"{home}/{relative_path}/credentials.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(asdict(creds)))


def get_credentials(relative_path=".nb_workflows/") -> Union[CredentialsRsp, None]:
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    try:
        with open(
            f"{home}/{relative_path}/credentials.json", "r", encoding="utf-8"
        ) as f:
            data = f.read()
            data_dict = json.loads(data)

            return CredentialsRsp(**data_dict)
    except FileNotFoundError:
        return None


def get_token_from_local(filepath: str):
    nbc = open_config(filepath)
    creds = get_credentials()
    if creds:
        v = validate_credentials(nbc.url_service, creds)
        if v:
            return token
    return login_cli(nbc.url_service)
