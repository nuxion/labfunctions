import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from labfunctions import defaults, errors, secrets
from labfunctions.context import create_notebook_ctx
from labfunctions.errors.generics import WorkflowRegisterClientError
from labfunctions.runtimes import local_runtime_data
from labfunctions.types import (
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
from labfunctions.types.workflows import WFCreateRsp, WFPushRsp
from labfunctions.utils import parse_var_line

from .base import BaseClient
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

    def workflows_push(
        self, refresh_workflows=True, update=False, wf_file=None
    ) -> WFPushRsp:
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
                        else:
                            errors.append(
                                WFCreateRsp(
                                    wfid=wd.wfid,
                                    alias=wd.alias,
                                    status_code=wr.status_code,
                                )
                            )
            except WorkflowRegisterClientError as e:
                self.logger.error(e)
                errors.append(
                    WFCreateRsp(wfid=wd.wfid, alias=wd.alias, status_code=503)
                )

        # self._workflows = _workflows
        if refresh_workflows:
            self.write(wf_file)
        return WFPushRsp(created=created, errors=errors)

    def workflows_list(self) -> List[WorkflowData]:
        r = self._http.get(f"/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def workflows_get(self, wfid) -> Union[WorkflowDataWeb, None]:
        r = self._http.get(f"/workflows/{self.projectid}/{wfid}")

        if r.status_code == 200:
            return WorkflowDataWeb(**r.json())
        return None

    def workflows_delete(self, wfid) -> int:
        r = self._http.delete(f"/workflows/{self.projectid}/{wfid}")
        # wd = self.state.find_by_id(wfid)
        # wd.wfid = None
        if r.status_code == 200:
            # self.sync_file()
            pass
        return r.status_code

    def workflows_enqueue(self, wfid) -> str:
        r = self._http.post(f"/workflows/{self.projectid}/_run/{wfid}")
        if r.status_code == 202:
            return r.json()["execid"]
        return ""

    def notebook_run(
        self,
        nb_name: str,
        params: Optional[Dict[str, Any]] = None,
        cluster=None,
        machine=None,
        runtime=None,
        version=None,
    ) -> ExecutionNBTask:

        task = NBTask(
            nb_name=nb_name,
            params=params,
            cluster=cluster,
            machine=machine,
            runtime=runtime,
            version=version,
        )
        rsp = self._http.post(
            f"/workflows/{self.projectid}/notebooks/_run", json=task.dict()
        )
        if rsp.status_code != 202:
            raise AttributeError(rsp.text)

        return ExecutionNBTask(**rsp.json())

    def build_context(
        self,
        wfid: str,
        runtime_name="default",
        runtimes_file="runtimes.yaml",
        version="latest",
    ) -> ExecutionNBTask:
        wf = self.state.find_by_id(wfid)
        rd = local_runtime_data(
            self.projectid, runtime_name, runtimes_file=runtimes_file, version=version
        )
        ctx = create_notebook_ctx(self.projectid, wf.nbtask, runtime=rd)
        return ctx
