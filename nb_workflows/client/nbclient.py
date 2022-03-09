import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Union

from nb_workflows import secrets
from nb_workflows.types import (
    ExecutionResult,
    HistoryRequest,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowsList,
)

from .base import BaseClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import store_credentials_disk, store_private_key


class NBClient(BaseClient):
    def workflows_create(self, t: NBTask) -> WFCreateRsp:
        self.auth_verify_or_refresh()
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

    def workflows_enqueue(self, jobid) -> str:
        self.auth_verify_or_refresh()
        r = self._http.post(f"{self._addr}/workflows/{self.projectid}/queue/{jobid}")
        if r.status_code == 202:
            return r.json()["execid"]

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

    def projects_agent_token(self) -> Union[Credentials, None]:
        self.auth_verify_or_refresh()
        r = self._http.post(f"{self._addr}/projects/{self.projectid}/_agent_token")

        if r.status_code == 200:
            return Credentials(**r.json())

        return None

    def projects_generate_dockerfile(self, docker_opts):
        root = Path.cwd()
        generate_dockerfile(root, docker_opts)

    def history_register(self, exec_result: ExecutionResult) -> bool:
        self.auth_verify_or_refresh()

        rsp = self._http.post(
            f"{self._addr}/history",
            json=asdict(exec_result),
        )

        if rsp.status_code == 201:
            return True
        return False

    def history_nb_output(self, exec_result: ExecutionResult) -> bool:
        """Upload the notebook from the execution result
        TODO: zip or compress notebook before upload.
        :return: True if ok, False if something fails.
        """
        self.auth_verify_or_refresh()
        logger = logging.getLogger(__name__)

        form_data = dict(output_name=exec_result.output_name)

        file_dir = f"{exec_result.output_dir}/{exec_result.output_name}"
        _addr = f"{self._addr}/history/{exec_result.projectid}/_output_ok"
        logger.warning(_addr)
        if exec_result.error:
            _addr = f"{self._addr}/history/{exec_result.projectid}/_output_fail"
            file_dir = f"{exec_result.error_dir}/{exec_result.output_name}"

        files = {"file": open(file_dir)}
        rsp = self._http.post(
            _addr,
            files=files,
            data=form_data,
        )
        if rsp.status_code == 201:
            return True
        return False
