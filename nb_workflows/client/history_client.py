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


class HistoryClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def history_register(self, exec_result: ExecutionResult) -> bool:

        rsp = self._http.post(
            f"/history",
            json=exec_result.dict(),
        )

        if rsp.status_code == 201:
            return True
        return False

    def history_get_last(self, wfid, last=1) -> List[HistoryResult]:
        rsp = self._http.get(f"/history/{self.projectid}/{wfid}?lt={last}")
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
        form_data = dict(output_name=exec_result.output_name)

        file_dir = f"{exec_result.output_dir}/{exec_result.output_name}"
        _addr = f"/history/{exec_result.projectid}/_output_ok"
        if exec_result.error:
            _addr = f"/history/{exec_result.projectid}/_output_fail"
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
