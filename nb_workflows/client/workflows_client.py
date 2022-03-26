import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nb_workflows import errors, secrets
from nb_workflows.conf import defaults
from nb_workflows.errors.generics import WorkflowRegisterClientError
from nb_workflows.types import (
    ExecutionNBTask,
    ExecutionResult,
    HistoryRequest,
    HistoryResult,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowDataWeb,
    WorkflowsList,
)
from nb_workflows.types.workflows import WFCreateRsp, WFPushRsp
from nb_workflows.utils import parse_var_line

from .base import BaseClient
from .types import Credentials, ProjectZipFile
from .uploads import generate_dockerfile
from .utils import get_private_key, store_credentials_disk, store_private_key


class WorkflowsClient(BaseClient):
    """Related to workflows"""

    def workflows_create(self, wd: WorkflowDataWeb) -> WFCreateRsp:
        r = self._http.post(
            f"/workflows/{self.projectid}",
            json=wd.dict(),
        )
        code = r.status_code
        if code == 200:
            self.logger.warning(f"Workflow {wd.wfid} already exist")
        if code == 400 or code == 503:
            raise WorkflowRegisterClientError(wd.wfid, self.projectid)

        return WFCreateRsp(
            status_code=r.status_code,
            alias=wd.alias,
            msg=r.json().get("msg"),
            wfid=r.json().get("wfid"),
        )

    def workflows_update(self, wd: WorkflowDataWeb) -> WFCreateRsp:
        r = self._http.put(
            f"/workflows/{self.projectid}",
            json=wd.dict(),
        )
        code = r.status_code
        if code == 400 or code == 503:
            raise WorkflowRegisterClientError(wd.wfid, self.projectid)

        return WFCreateRsp(
            status_code=r.status_code,
            alias=wd.alias,
            msg=r.json().get("msg"),
            wfid=r.json().get("wfid"),
        )

    def workflows_push(self, refresh_workflows=True, update=False) -> WFPushRsp:
        _workflows = self.state.snapshot()
        errors = []
        created = []
        for _, wd in _workflows.workflows.items():
            try:
                if update:
                    wr = self.workflows_update(wd)
                    created.append(wr)
                else:
                    if not wd.wfid:
                        wr = self.workflows_create(wd)
                        if wr.status_code == 200:
                            self.logger.warning(f"Workflow {wd.alias} already exist")
                        elif wr.status_code == 201:
                            created.append(wr)
                            if refresh_workflows:
                                wd.wfid = wr.wfid
                                self.state.add_workflow(wd)
            except WorkflowRegisterClientError as e:
                self.logger.error(e)
                errors.append(
                    WFCreateRsp(wfid=wd.wfid, alias=wd.alias, status_code=503)
                )

        # self._workflows = _workflows
        if refresh_workflows:
            self.write()
        return WFPushRsp(created=created, errors=errors)

    def workflows_list(self) -> List[WorkflowData]:
        r = self._http.get(f"/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def workflows_get(self, wfid) -> Union[WorkflowDataWeb, None]:
        r = self._http.get(f"/workflows/{self.projectid}/{wfid}")

        if r.status_code == 200:
            return WorkflowDataWeb(**r.json())
        if r.status_code == 404:
            return None

    def workflows_delete(self, wfid) -> int:
        r = self._http.delete(f"/workflows/{self.projectid}/{wfid}")
        wd = self.state.find_by_id(wfid)
        wd.wfid = None
        if r.status_code == 200:
            # self.sync_file()
            pass
        return r.status_code

    def workflows_enqueue(self, wfid) -> str:
        r = self._http.post(f"/workflows/{self.projectid}/queue/{wfid}")
        if r.status_code == 202:
            return r.json()["execid"]

    def notebook_run(
        self,
        nb_name: str,
        params: Optional[Dict[str, Any]] = None,
        machine=None,
        docker_version=None,
    ) -> ExecutionNBTask:

        task = NBTask(
            nb_name=nb_name,
            params=params,
            machine=machine,
            docker_version=docker_version,
        )
        rsp = self._http.post(
            f"/workflows/{self.projectid}/notebooks/_run", json=task.dict()
        )
        if rsp.status_code != 202:
            raise AttributeError(rsp.text)

        return ExecutionNBTask(**rsp.json())
