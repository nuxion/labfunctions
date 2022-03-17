import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nb_workflows import errors, secrets
from nb_workflows.conf import defaults
from nb_workflows.types import (
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
from nb_workflows.utils import parse_var_line

from .base import BaseClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import get_private_key, store_credentials_disk, store_private_key


class ProjectsClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def workflows_create(self, wd: WorkflowDataWeb) -> WFCreateRsp:
        r = self._http.post(
            f"/workflows/{self.projectid}",
            json=wd.dict(),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            wfid=r.json().get("wfid"),
        )

    def workflows_update(self, wd: WorkflowDataWeb) -> WFCreateRsp:
        r = self._http.put(
            f"/workflows/{self.projectid}",
            json=wd.dict(),
        )

        return WFCreateRsp(
            status_code=r.status_code,
            msg=r.json().get("msg"),
            wfid=r.json().get("wfid"),
        )

    def workflows_push(self, refresh_workflows=True, update=False):
        _workflows = self.state.snapshot()
        for _, wd in _workflows.workflows.items():
            if update:
                r = self.workflows_update(wd)
            else:
                if not wd.wfid:
                    r = self.workflows_create(wd)
                    if r.status_code == 200:
                        print(f"Workflow {wd.alias} already exist")
                    elif r.status_code == 201:
                        print(f"Workflow {wd.alias} created. Jobid: {r.wfid}")
                        if refresh_workflows:
                            wd.wfid = r.wfid
                            self.state.add_workflow(wd)

        # self._workflows = _workflows
        if refresh_workflows:
            self.write()

    def workflows_list(self) -> List[WorkflowData]:
        r = self._http.get(f"/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]

    def workflows_get(self, wfid) -> Union[WorkflowData, None]:
        r = self._http.get(f"/workflows/{self.projectid}/{wfid}")

        if r.status_code == 200:
            return WorkflowData(**r.json())
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def workflows_delete(self, wfid) -> int:
        r = self._http.delete(f"/workflows/{self.projectid}/{wfid}")
        if r.status_code == 200:
            # self.sync_file()
            pass
        return r.status_code

    def workflows_enqueue(self, wfid) -> str:
        r = self._http.post(f"/workflows/{self.projectid}/queue/{wfid}")
        if r.status_code == 202:
            return r.json()["execid"]
