from dataclasses import asdict
from typing import Dict, List, Optional, Union

from nb_workflows import secrets
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
from nb_workflows.uploads import ProjectZipFile

from .base import AbstractClient
from .types import Credentials, WFCreateRsp
from .utils import store_private_key


class NBClient(AbstractClient):
    def __init__(
        self,
        url_service: str,
        projectid: str,
        creds: Credentials,
        project: Optional[ProjectData] = None,
        workflows: Optional[List[NBTask]] = None,
        version="0.1.0",
    ):

        super().__init__(url_service, projectid, creds, project, workflows, version)

    def workflows_create(self, t: NBTask) -> WFCreateRsp:
        r = self._http.post(
            f"{self._addr}/workflows/{self.projectid}",
            json=asdict(t),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def workflows_update(self, t: NBTask) -> WFCreateRsp:
        self.auth_verify_or_refresh()
        r = self._http.put(
            f"{self._addr}/workflows/{self.projectid}",
            json=asdict(t),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def workflows_push(self, refresh_workflows=True, update=False):
        self.auth_verify_or_refresh()
        _workflows = []
        for task in self._workflows:
            if update:
                r = self.workflows_update(task)
            else:
                if not task.jobid:
                    r = self.workflows_create(task)
                    if r.status_code == 200:
                        print(f"Workflow {task.alias} already exist")
                    elif r.status_code == 201:
                        print(f"Workflow {task.alias} created. Jobid: {r.jobid}")
                        if refresh_workflows:
                            task.jobid = r.jobid

        # self._workflows = _workflows
        if refresh_workflows:
            self.sync_file()

    def workflows_list(self) -> List[WorkflowData]:
        self.auth_verify_or_refresh()
        r = self._http.get(f"{self._addr}/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def workflows_get(self, jobid) -> Union[WorkflowData, None]:
        self.auth_verify_or_refresh()
        r = self._http.get(f"{self._addr}/workflows/{self.projectid}/{jobid}")

        if r.status_code == 200:
            return WorkflowData(**r.json())
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def workflows_delete(self, jobid) -> int:
        self.auth_verify_or_refresh()
        r = self._http.delete(f"{self._addr}/workflows/{self.projectid}/{jobid}")
        if r.status_code == 200:
            self.sync_file()
        return r.status_code

    def projects_create(self) -> Union[ProjectData, None]:
        self.auth_verify_or_refresh()

        _key = secrets.generate_private_key()
        pq = ProjectReq(
            name=self.wf_file.project.name,
            private_key=_key,
            projectid=self.wf_file.project.projectid,
            description=self.wf_file.project.description,
            repository=self.wf_file.project.repository,
        )
        r = self._http.post(
            f"{self._addr}/projects",
            json=asdict(pq),
        )
        if r.status_code == 200:
            print("Project already exist")
        elif r.status_code == 201:
            print("Project created")
            pd = ProjectData(**r.json())
            store_private_key(_key, pd.projectid)
            return pd
        else:
            raise TypeError("Something went wrong creating the project %s", r.text)
        return None

    def projects_get(self) -> Union[ProjectData, None]:
        self.auth_verify_or_refresh()
        r = self._http.get(f"{self._addr}/projects/{self.projectid}")
        if r.status_code == 200:
            return ProjectData(**r.json())
        return None

    def projects_upload(self, zfile: ProjectZipFile):
        self.auth_verify_or_refresh()
        files = {"file": open(zfile.filepath, "rb")}
        r = self._http.post(
            f"{self._addr}/projects/{self.projectid}/_upload", files=files
        )
        print(r.status_code)
