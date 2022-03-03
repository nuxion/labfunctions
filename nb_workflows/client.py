import getpass
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import httpx
import jwt

from nb_workflows.conf import settings_client as settings
from nb_workflows.utils import get_parent_folder, open_toml, write_toml
from nb_workflows.workflows import projects
from nb_workflows.workflows.entities import (ExecutionResult, HistoryRequest,
                                             NBTask, ProjectData, ProjectReq,
                                             ScheduleData)


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
    """ Validates against the REST API server """
    _headers = {"Authorization": f"Bearer {token}"}

    r = httpx.get(f"{websrv}/auth/verify", headers=_headers)
    if r.status_code == 200:
        return True
    if r.status_code == 401:
        return False
    raise TypeError("Wrong communitacion against {websrv}")


def validate_credentials_local(token) -> bool:
    """ Validates locally against the jwt signature
    If exp is not bigger than now, then is valid.
    """
    n = datetime.utcnow()
    ts_now = int(datetime.timestamp(n))
    tkn_dict = jwt.decode(token,
                          options={"verify_signature": False})

    if ts_now < tkn_dict["exp"]:
        return True
    return False


def create_empty_workfile(projectid, name,
                          tasks: Optional[List[NBTask]] = None,
                          version="0.1.0") -> WorkflowsFile:
    pd = ProjectData(
        name=name,
        projectid=projectid
    )
    wf = WorkflowsFile(project=pd, version=version)
    if tasks:
        wf.workflows = tasks
    return wf


class NBClient:
    """NB Workflow client"""

    def __init__(self, url_service: str,
                 projectid: str,
                 creds: Credentials,
                 workflow_file: Optional[WorkflowsFile] = None):
        self._addr = url_service
        self.projectid = projectid
        self._workflows: Optional[List[NBTask]] = None
        if workflow_file:
            self._workflows = workflow_file.workflows
        self.creds = creds
        self.wf_file: Optional[WorkflowsFile] = workflow_file
        self._headers = {"Authorization": f"Bearer {creds.access_token}"}

    @property
    def project_data(self) -> ProjectData:
        return self.wf_file.project

    def sync_file(self):
        rsp = httpx.get(
            f"{self._addr}/workflows/{self.projectid}/schedule",
            headers=self._headers
        )
        workflows = rsp.json()
        tasks = [NBTask(**w["job_detail"]) for w in workflows]
        self._workflows = tasks
        self.write()

    def refresh(self):
        r = httpx.post(f"{self._addr}/auth/refresh",
                       json={"refresh_token": self.creds.refresh_token},
                       headers=self._headers)
        data = r.json()
        self.creds.access_token = data["access_token"]
        store_credentials(self.creds)

    def verify_or_refresh(self) -> bool:
        valid = validate_credentials_local(self.creds.access_token)
        if not valid:
            self.refresh()
            return True
        return False

    def write(self, output="workflows.toml"):
        self.wf_file.workflows = self._workflows
        write_toml(output, asdict(self.wf_file))

    def create_workflow(self, t: NBTask) -> WFCreateRsp:
        r = httpx.post(
            f"{self._addr}/workflows/{self.projectid}/schedule",
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
            f"{self._addr}/workflows/{self.projectid}/schedule",
            json=asdict(t),
            headers=self._headers,
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
            self.sync_file()

    def list_scheduled(self) -> List[ScheduleListRsp]:
        self.verify_or_refresh()
        r = httpx.get(f"{self._addr}/workflows/{self.projectid}/schedule",
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
        r = httpx.get(f"{self._addr}/workflows/{self.projectid}/schedule/{jobid}",
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
            f"{self._addr}/workflows/{self.projectid}/schedule/rqjobs/_cancel/{jobid}",
            headers=self._headers
        )
        if r.status_code != 200:
            raise TypeError("Something went wrong with %s", jobid)
        return r.status_code

    def execute_remote(self, jobid) -> ScheduleExecRsp:
        self.verify_or_refresh()
        r = httpx.post(
            f"{self._addr}/workflows/{self.projectid}/schedule/{jobid}/_run",
            headers=self._headers
        )
        return ScheduleExecRsp(r.status_code, executionid=r.json()["executionid"])

    def delete(self, jobid) -> int:
        self.verify_or_refresh()
        r = httpx.delete(
            f"{self._addr}/workflows/{self.projectid}/schedule/{jobid}",
            headers=self._headers
        )
        if r.status_code == 200:
            self.sync_file()
        return r.status_code

    def history_last(self, jobid):
        self.verify_or_refresh()
        r = httpx.get(
            f"{self._addr}/workflows/{self.projectid}/history/{jobid}", headers=self._headers
        )
        return r.json()

    def rq_status(self, jobid):
        self.verify_or_refresh()
        r = httpx.get(
            f"{self._addr}/workflows/rqjobs/{jobid}", headers=self._headers
        )
        return r.json()

    def register_history(self, execution_result: ExecutionResult, nb_task: NBTask):
        self.verify_or_refresh()
        req = HistoryRequest(task=nb_task, result=execution_result)
        r = httpx.post(f"{self._addr}/history", json=asdict(req),
                       headers=self._headers)
        return r.json()

    def create_project(self) -> Union[ProjectData, None]:
        pq = ProjectReq(
            name=self.wf_file.project.name,
            projectid=self.wf_file.project.projectid,
            description=self.wf_file.project.description,
            repository=self.wf_file.project.repository,
        )
        r = httpx.post(
            f"{self._addr}/projects",
            json=asdict(pq),
            headers=self._headers
        )
        if r.status_code == 200:
            print("Project already exist")
        elif r.status_code == 201:
            print("Project created")
            return ProjectData(**r.json())
        else:
            raise TypeError(
                "Something went wrong creating the project %s", r.text)


def minimal_client(url_service, creds: Credentials) -> Union[NBClient, None]:
    wf_file = create_empty_workfile("", "")

    nb_client = NBClient(creds=creds, url_service=url_service,
                         projectid="",
                         workflow_file=wf_file)
    return nb_client


def init(url_service,
         example=True, version="0.1.0") -> NBClient:

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

    wf_file = create_empty_workfile(projectid, name, tasks=tasks)

    nb_client = NBClient(creds=creds, url_service=url_service,
                         projectid=projectid,
                         workflow_file=wf_file)

    create = str(input("Create project in the server? (Y/n): ") or "y")
    if create.lower() == 'y':
        nb_client.create_project()
    nb_client.write()

    return nb_client


def open_workflows_file(filepath) -> WorkflowsFile:
    data_dict = open_toml(filepath)
    wf = WorkflowsFile(**data_dict)
    if wf.project:
        wf.project = ProjectData(**data_dict["project"])
    if wf.workflows:
        wf.workflows = [NBTask(**w)
                        for w in data_dict["workflows"]]
    return wf


def from_file(filepath) -> NBClient:
    wf = open_workflows_file(filepath)

    creds = get_credentials()

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        projectid=wf.project.projectid,
        creds=creds,
        workflow_file=wf
    )


def from_settings() -> NBClient:
    creds = Credentials(access_token=settings.CLIENT_TOKEN,
                        refresh_token=settings.CLIENT_REFRESH_TOKEN)

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        projectid=settings.PROJECTID)


# def from_remote(url_service, token, version="0.1.0") -> NBClient:
#     headers = {"Authorization": f"Bearer {token}"}
#     r = httpx.get(f"{url_service}/workflows/schedule", headers=headers)
#     workflows = []
#     for w_data in r.json():
#         obj = NBTask(**w_data["job_detail"])
#         obj.jobid = w_data["jobid"]
#         workflows.append(obj)
#     nbc = NBCliConfig(url_service, version, workflows=workflows)
#     return NBClient(token, nbc)


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
