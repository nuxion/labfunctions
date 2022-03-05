import getpass
import json
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx
import jwt
import yaml

from nb_workflows.conf import settings_client as settings
from nb_workflows.core.entities import (
    ExecutionResult,
    HistoryRequest,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowsList,
)
from nb_workflows.core.managers import projects
from nb_workflows.utils import (
    get_parent_folder,
    open_toml,
    open_yaml,
    write_toml,
    write_yaml,
)


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


@dataclass
class WorkflowsFile:
    project: ProjectData
    version: str = "0.1"
    # workflows: Optional[Dict[str, NBTask]] = None
    workflows: Optional[List[NBTask]] = None


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
class Credentials:
    access_token: str
    refresh_token: Optional[str] = None


def validate_credentials_remote(websrv, token) -> bool:
    """Validates against the REST API server"""
    _headers = {"Authorization": f"Bearer {token}"}

    r = httpx.get(f"{websrv}/auth/verify", headers=_headers)
    if r.status_code == 200:
        return True
    if r.status_code == 401:
        return False
    raise TypeError("Wrong communitacion against {websrv}")


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


def create_empty_workfile(
    projectid, name, tasks: Optional[List[NBTask]] = None, version="0.1.0"
) -> WorkflowsFile:
    pd = ProjectData(name=name, projectid=projectid)
    wf = WorkflowsFile(project=pd, version=version)
    if tasks:
        wf.workflows = {t.alias: t for t in tasks}
    return wf


class NBClient:
    """NB Workflow client"""

    def __init__(
        self,
        url_service: str,
        projectid: str,
        creds: Credentials,
        project: Optional[ProjectData] = None,
        workflows: Optional[List[NBTask]] = None,
        version="0.1.0",
    ):

        self.projectid = projectid
        self.creds = creds

        self._addr = url_service
        self._workflows = workflows
        self._project = project
        self._headers = {"Authorization": f"Bearer {creds.access_token}"}
        self._version = version

    @property
    def wf_file(self) -> WorkflowsFile:
        return WorkflowsFile(
            version=self._version,
            project=self._project,
            # workflows={w.alias: w for w in self._workflows}
            workflows=self._workflows,
        )

    def sync_file(self):

        wfs = self.list_workflows()
        tasks = []
        for w in wfs:
            task = NBTask(**w.job_detail)
            if w.job_detail.get("schedule"):
                task.schedule = ScheduleData(**w.job_detail["schedule"])
            tasks.append(task)

        self._workflows = tasks
        self.write()

    def refresh(self):
        r = httpx.post(
            f"{self._addr}/auth/refresh",
            json={"refresh_token": self.creds.refresh_token},
            headers=self._headers,
        )
        data = r.json()
        self.creds.access_token = data["access_token"]
        store_credentials(self.creds)

    def verify_or_refresh(self) -> bool:
        valid = validate_credentials_local(self.creds.access_token)
        if not valid:
            self.refresh()
            return True
        return False

    def write(self, output="workflows.yaml"):
        # write_toml(output, asdict(self.wf_file))
        write_yaml("workflows.yaml", asdict(self.wf_file))
        # with open("workflows.yaml", "w") as f:
        #     f.write(yaml.dump(asdict(self.wf_file)))

    @staticmethod
    def read(filepath="workflows.yaml") -> WorkflowsFile:
        # data_dict = open_toml(filepath)
        data_dict = open_yaml(filepath)

        wf = WorkflowsFile(**data_dict)
        if wf.project:
            wf.project = ProjectData(**data_dict["project"])
        if wf.workflows:
            # _wfs = data_dict["workflows"]
            # wf.workflows = {_wfs[k]["alias"]: NBTask(**_wfs[k])
            #                for k in _wfs.keys()}
            wf.workflows = [NBTask(**w) for w in data_dict["workflows"]]
        return wf

    def create_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.post(
            f"{self._addr}/workflows/{self.projectid}",
            json=asdict(t),
            headers=self._headers,
            timeout=None,
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def update_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.put(
            f"{self._addr}/workflows/{self.projectid}",
            json=asdict(t),
            headers=self._headers,
            timeout=None,
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def push_workflows(self, refresh_workflows=True, update=False):
        self.verify_or_refresh()
        _workflows = []
        for task in self._workflows:
            if update:
                r = self.update_workflow(task)
            else:
                if not task.jobid:
                    r = self.create_workflow(task)
                    if r.status_code == 200:
                        print(f"Workflow {task.alias} already exist")
                    elif r.status_code == 201:
                        print(f"Workflow {task.alias} created. Jobid: {r.jobid}")
                        if refresh_workflows:
                            task.jobid = r.jobid

        # self._workflows = _workflows
        if refresh_workflows:
            self.sync_file()

    def list_workflows(self) -> List[WorkflowData]:
        self.verify_or_refresh()
        r = httpx.get(f"{self._addr}/workflows/{self.projectid}", headers=self._headers)

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def get_workflow(self, jobid) -> Union[WorkflowData, None]:
        self.verify_or_refresh()
        r = httpx.get(
            f"{self._addr}/workflows/{self.projectid}/{jobid}",
            headers=self._headers,
        )
        if r.status_code == 200:
            data_dict = r.json()
            # task = NBTask(**data_dict['job_detail'])
            # task.jobid = jobid
            # task.schedule = ScheduleData(**data_dict["job_detail"]["schedule"])

            # return WorkflowRsp(task=task, enabled=data_dict["enabled"])
            return WorkflowData(**r.json())
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def rq_cancel_job(self, jobid) -> int:
        r = httpx.delete(
            f"{self._addr}/rqjobs/{self.projectid}/_cancel/{jobid}",
            headers=self._headers,
        )
        if r.status_code != 200:
            raise TypeError("Something went wrong with %s", jobid)
        return r.status_code

    def execute_remote(self, jobid) -> ScheduleExecRsp:
        self.verify_or_refresh()
        r = httpx.post(
            f"{self._addr}/workflows/{self.projectid}/schedule/{jobid}/_run",
            headers=self._headers,
        )
        return ScheduleExecRsp(r.status_code, executionid=r.json()["executionid"])

    def delete(self, jobid) -> int:
        self.verify_or_refresh()
        r = httpx.delete(
            f"{self._addr}/workflows/{self.projectid}/{jobid}",
            headers=self._headers,
        )
        if r.status_code == 200:
            self.sync_file()
        return r.status_code

    def history_last(self, jobid):
        self.verify_or_refresh()
        r = httpx.get(
            f"{self._addr}/workflows/{self.projectid}/history/{jobid}",
            headers=self._headers,
        )
        return r.json()

    def rq_status(self, jobid):
        self.verify_or_refresh()
        r = httpx.get(f"{self._addr}/workflows/rqjobs/{jobid}", headers=self._headers)
        return r.json()

    def register_history(self, execution_result: ExecutionResult, nb_task: NBTask):
        self.verify_or_refresh()
        req = HistoryRequest(task=nb_task, result=execution_result)
        r = httpx.post(f"{self._addr}/history", json=asdict(req), headers=self._headers)
        return r.json()

    def create_project(self) -> Union[ProjectData, None]:
        pq = ProjectReq(
            name=self.wf_file.project.name,
            projectid=self.wf_file.project.projectid,
            description=self.wf_file.project.description,
            repository=self.wf_file.project.repository,
        )
        r = httpx.post(f"{self._addr}/projects", json=asdict(pq), headers=self._headers)
        if r.status_code == 200:
            print("Project already exist")
        elif r.status_code == 201:
            print("Project created")
            return ProjectData(**r.json())
        else:
            raise TypeError("Something went wrong creating the project %s", r.text)
        return None


def init(url_service, example=True, version="0.1.0") -> NBClient:

    tasks = None
    if example:
        tasks = [_example_task()]

    creds = login_cli(url_service)
    projectid = settings.PROJECTID
    name = settings.PROJECT_NAME
    if not projectid:
        name = projects.ask_project_name()
        rsp = httpx.get(f"{settings.WORKFLOW_SERVICE}/projects/_generateid")
        projectid = rsp.json()["projectid"]

    # wf_file = create_empty_workfile(projectid, name, tasks=tasks)

    nb_client = NBClient(
        creds=creds,
        url_service=url_service,
        projectid=projectid,
        project=ProjectData(name=name, projectid=projectid),
        workflows=tasks,
        version=version,
    )

    create = str(input("Create project in the server? (Y/n): ") or "y")
    if create.lower() == "y":
        nb_client.create_project()
    nb_client.write()

    return nb_client


def minimal_client(url_service, token, refresh, projectid) -> NBClient:
    creds = Credentials(access_token=token, refresh_token=refresh)
    return NBClient(url_service=url_service, creds=creds, projectid=projectid)


def from_file(filepath) -> NBClient:
    wf = NBClient.read(filepath)
    # tasks = [wf.workflows[k] for k in wf.workflows.keys()]
    creds = get_credentials()

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        projectid=wf.project.projectid,
        creds=creds,
        project=wf.project,
        workflows=wf.workflows,
    )


def from_settings() -> NBClient:
    creds = Credentials(
        access_token=settings.CLIENT_TOKEN,
        refresh_token=settings.CLIENT_REFRESH_TOKEN,
    )

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        projectid=settings.PROJECTID,
        project=ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID),
    )


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


def store_credentials(creds: Credentials, relative_path=".nb_workflows/"):
    home = str(Path.home())
    Path(f"{home}/{relative_path}").mkdir(parents=True, exist_ok=True)
    with open(f"{home}/{relative_path}/credentials.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(asdict(creds)))


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
