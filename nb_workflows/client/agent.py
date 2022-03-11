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

    def projects_private_key(self) -> Union[str, None]:
        """Gets private key to be shared to the docker container of a
        workflow task
        """
        self.auth_verify_or_refresh()
        r = self._http.get(f"{self._addr}/projects/{self.projectid}/_private_key")

        if r.status_code == 200:
            key = r.json()["private_key"]
            return key
        return None

    def history_register(self, exec_result: ExecutionResult) -> bool:
        self.auth_verify_or_refresh()

        rsp = self._http.post(
            f"{self._addr}/history",
            json=exec_result.dict(),
        )

        if rsp.status_code == 201:
            return True
        return False
