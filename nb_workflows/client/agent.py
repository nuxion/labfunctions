import os
from typing import Union

from nb_workflows.conf.types import ServerSettings
from nb_workflows.types import WorkflowData

from .base import BaseClient
from .types import Credentials, ExecutionResult, WFCreateRsp


class AgentClient(BaseClient):
    """
    It is used in each machine running a agent (data plane),
    and is used to communicates with server for workflows task
    preparations.
    """

    def workflows_get(self, wfid) -> Union[WorkflowData, None]:
        r = self._http.get(f"/workflows/{self.projectid}/{wfid}")

        if r.status_code == 200:
            return WorkflowData(**r.json())
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise KeyError("Invalid auth")
        raise TypeError("Something went wrong %s", r.text)

    def projects_private_key(self) -> Union[str, None]:
        """Gets private key to be shared to the docker container of a
        workflow task
        """
        r = self._http.get(f"/projects/{self.projectid}/_private_key")

        if r.status_code == 200:
            key = r.json()["private_key"]
            return key
        return None

    def history_register(self, exec_result: ExecutionResult) -> bool:

        rsp = self._http.post(
            f"/history",
            json=exec_result.dict(),
        )

        if rsp.status_code == 201:
            return True
        return False
