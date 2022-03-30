import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nb_workflows import errors, secrets
from nb_workflows.conf import defaults
from nb_workflows.errors.client import ProjectUploadError
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
from nb_workflows.types.projects import ProjectBuildReq, ProjectBuildResp
from nb_workflows.types.users import AgentReq
from nb_workflows.utils import parse_var_line

from .base import BaseClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import get_private_key, store_credentials_disk, store_private_key


class ProjectsClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def projects_create(self) -> Union[ProjectData, None]:
        raise IndexError()
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
        if r.status_code != 201:
            raise ProjectUploadError(self.projectid)

    def projects_build(self, name) -> ProjectBuildResp:
        pbr = ProjectBuildReq(name=name)
        rsp = self._http.post(f"/projects/{self.projectid}/_build", json=pbr.dict())
        return ProjectBuildResp(**rsp.json())

    def projects_create_agent(self) -> Union[str, None]:
        r = self._http.post(f"/projects/{self.projectid}/agent")

        if r.status_code == 201:
            return r.json()["msg"]

        return None

    def projects_agent_token(self) -> Union[Credentials, None]:
        r = self._http.post(f"/projects/{self.projectid}/agent/_token")

        if r.status_code == 200:
            return Credentials(**r.json())

        return None

    def projects_private_key(self) -> Union[str, None]:
        """Gets private key to be shared to the docker container of a
        workflow task
        """
        r = self._http.get(f"/projects/{self.projectid}/_private_key")

        if r.status_code == 200:
            key = r.json()["private_key"]
            return key
        return None
