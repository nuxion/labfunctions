import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Union

from nb_workflows import errors, secrets
from nb_workflows.types import (
    ExecutionResult,
    HistoryRequest,
    HistoryResult,
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
from .utils import get_private_key, store_credentials_disk, store_private_key


class NBClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def workflows_create(self, t: NBTask) -> WFCreateRsp:
        r = self._http.post(
            f"/workflows/{self.projectid}",
            json=t.dict(),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def workflows_update(self, t: NBTask) -> WFCreateRsp:
        r = self._http.put(
            f"/workflows/{self.projectid}",
            json=t.dict(),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            jobid=r.json().get("jobid"),
        )

    def workflows_push(self, refresh_workflows=True, update=False):
        _workflows = []
        for task in self.state.workflows:
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
            pass
            # self.sync_file()

    def workflows_list(self) -> List[WorkflowData]:
        r = self._http.get(f"/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def workflows_get(self, jobid) -> Union[WorkflowData, None]:
        r = self._http.get(f"/workflows/{self.projectid}/{jobid}")

        if r.status_code == 200:
            return WorkflowData(**r.json())
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def workflows_delete(self, jobid) -> int:
        r = self._http.delete(f"/workflows/{self.projectid}/{jobid}")
        if r.status_code == 200:
            # self.sync_file()
            pass
        return r.status_code

    def workflows_enqueue(self, jobid) -> str:
        r = self._http.post(f"/workflows/{self.projectid}/queue/{jobid}")
        if r.status_code == 202:
            return r.json()["execid"]

    def projects_create(self) -> Union[ProjectData, None]:
        _key = secrets.generate_private_key()
        pq = ProjectReq(
            name=self.state.project.name,
            private_key=_key,
            projectid=self.state.project.projectid,
            description=self.state.project.description,
            repository=self.state.project.repository,
        )
        r = self._http.post(
            f"/projects",
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
        r = self._http.get(f"/projects/{self.projectid}")
        if r.status_code == 200:
            return ProjectData(**r.json())
        return None

    def projects_upload(self, zfile: ProjectZipFile):
        files = {"file": open(zfile.filepath, "rb")}
        r = self._http.post(f"/projects/{self.projectid}/_upload", files=files)
        print(r.status_code)

    def projects_agent_token(self) -> Union[Credentials, None]:
        r = self._http.post(f"/projects/{self.projectid}/_agent_token")

        if r.status_code == 200:
            return Credentials(**r.json())

        return None

    def projects_private_key(self) -> str:
        """Gets private key to be shared to the docker container of a
        workflow task
        """
        r = self._http.get(f"/projects/{self.projectid}/_private_key")

        key = None
        if r.status_code == 200:
            key = r.json().get("private_key")
        if not key:
            raise errors.PrivateKeyNotFound(self.projectid)

        store_private_key(key, self.projectid)
        return key

    def get_private_key(self) -> str:
        """shortcut for getting a private key locally
        TODO: separate command line cli from a general client and an agent client
        a command line cli has filesystem side effects and a agent client not"""
        key = get_private_key(self.projectid)
        if not key:
            return self.projects_private_key()
        return key

    def projects_generate_dockerfile(self, docker_opts):
        root = Path.cwd()
        generate_dockerfile(root, docker_opts)

    def history_register(self, exec_result: ExecutionResult) -> bool:

        rsp = self._http.post(
            f"/history",
            json=exec_result.dict(),
        )

        if rsp.status_code == 201:
            return True
        return False

    def history_get_last(self, jobid, last=1) -> List[HistoryResult]:
        rsp = self._http.get(f"/history/{self.projectid}/{jobid}?lt={last}")
        rows = []
        for r in rsp.json()["rows"]:
            h = HistoryResult(**r)
            h.result = ExecutionResult(**r["result"])
            rows.append(h)

        return rows

    def history_nb_output(self, exec_result: ExecutionResult) -> bool:
        """Upload the notebook from the execution result
        TODO: zip or compress notebook before upload.
        :return: True if ok, False if something fails.
        """
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
