from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

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


class NBClient:
    """ NB Workflow client """

    def __init__(self, conf: NBCliConfig):
        self._data = conf
        self._workflows = conf.workflows
        self._addr = conf.url_service

    def write(self, output="workflows.toml"):
        with open(output, "w", encoding="utf-8") as f:
            _dump = toml.dumps(asdict(self._data))
            f.write(_dump)

    def create_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.post(f"{self._addr}/workflows/schedule", json=asdict(t))

        return WFCreateRsp(status_code=r.status_code,
                           msg=r.json().get("msg"),
                           jobid=r.json().get("jobid"))

    def push_all(self, refresh_workflows=True):
        for task in self._workflows:
            r = self.create_workflow(task)
            if r.status_code == 200:
                print(f"Workflow {task.schedule['alias']} already exist")
            elif r.status_code == 201:
                print(
                    f"Workflow {task.schedule['alias']} created. Jobid: {r.jobid}")
                if refresh_workflows:
                    task.jobid = r.jobid

        if refresh_workflows:
            self.write()

    def list_scheduled(self) -> List[ScheduleListRsp]:
        r = httpx.get(f"{self._addr}/workflows/schedule")
        data = [ScheduleListRsp(
            nb_name=s["nb_name"],
            jobid=s["jobid"],
            enabled=s["enabled"],
            description=s.get("description"),

        ) for s in r.json()]
        return data

    def execute_remote(self, jobid) -> ScheduleExecRsp:
        r = httpx.post(f"{self._addr}/workflows/schedule/{jobid}/_run")
        return ScheduleExecRsp(r.status_code,
                               executionid=r.json()["executionid"])

    def delete(self, jobid) -> int:
        r = httpx.delete(f"{self._addr}/workflows/schedule/{jobid}")
        return r.status_code


def init(url_service, version="0.1.0") -> NBClient:
    t = NBTask(nb_name="test_workflow",
               description="An example of how to configure a specific workflow",
               params=dict(TIMEOUT=5),
               schedule=ScheduleData(
                   alias="notebook.example",
                   repeat=1,
                   interval=10,
               ))
    nbc = NBCliConfig(version=version, url_service=url_service,
                      workflows=[t])

    return NBClient(nbc)


def from_file(filepath) -> NBClient:
    data_dict = _open_toml(filepath)
    nbc = NBCliConfig(**data_dict)
    nbc.workflows = [NBTask(**w) for w in data_dict["workflows"]]
    obj = NBClient(nbc)

    return obj
