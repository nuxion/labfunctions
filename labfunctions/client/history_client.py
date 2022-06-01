import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

from labfunctions import defaults, errors, secrets, types
from labfunctions.log import client_logger
from labfunctions.utils import parse_var_line

from .base import BaseClient
from .utils import get_private_key, store_credentials_disk, store_private_key


class HistoryClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def history_register(self, exec_result: types.ExecutionResult) -> bool:

        rsp = self._http.post(
            f"/history",
            json=exec_result.dict(),
        )

        if rsp.status_code == 201:
            return True
        return False

    def history_get_last(
        self, wfid: Optional[str] = None, last=1
    ) -> List[types.HistoryResult]:
        query = f"/history/{self.projectid}?lt={last}"
        if wfid:
            query = f"/history/{self.projectid}/{wfid}?lt={last}"
        rsp = self._http.get(query)
        if rsp.status_code == 404:
            return []
        rows = []
        for r in rsp.json()["rows"]:
            h = types.HistoryResult(**r)
            h.result = types.ExecutionResult(**r["result"])
            rows.append(h)

        return rows

    def history_detail(self, execid: str) -> Union[types.HistoryResult, None]:
        query = f"/history/{self.projectid}/detail/{execid}"
        rsp = self._http.get(query)
        if rsp.status_code == 200:
            return types.HistoryResult(**rsp.json())
        return None

    def history_get_output(self, uri) -> Generator[bytes, None, None]:
        """uri if ok:
        uri = f"{row.result.output_dir}/{row.result.output_name}"
        else:
        uri = f"{row.result.error_dir}/{row.result.output_name}"
        """
        url = f"/history/{self.projectid}/_get_output?file={uri}"
        with self._http.stream("GET", url) as r:
            if r.status_code == 200:
                for data in r.iter_bytes():
                    yield data
            else:
                raise errors.HistoryNotebookError(self._addr, uri)

    def history_nb_output(self, exec_result: types.ExecutionResult) -> bool:
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

    def task_status(self, execid: str) -> Union[types.TaskStatus, None]:
        rsp = self._http.get(f"/history/{self.projectid}/task/{execid}")
        if rsp.status_code == 200:
            return types.TaskStatus(**rsp.json())
        return None
