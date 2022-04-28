import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nb_workflows import defaults, errors, secrets
from nb_workflows.errors.client import ProjectCreateError, ProjectUploadError
from nb_workflows.errors.runtimes import RuntimeCreationError
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
from nb_workflows.types.docker import RuntimeVersionData
from nb_workflows.types.projects import (
    ProjectBuildReq,
    ProjectBuildResp,
    ProjectCreated,
)
from nb_workflows.types.user import AgentReq
from nb_workflows.utils import binary_file_reader, parse_var_line

from .base import BaseClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import get_private_key, store_credentials_disk, store_private_key


class ProjectsClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def projects_create(
        self,
        name: str,
        desc: Optional[str] = None,
        repository: Optional[str] = None,
        store_key: bool = True,
    ) -> Union[ProjectCreated, None]:
        """
        A staless project creator it don't use any internal state of the client
        instead, all values should be provided in this method for a project to be
        created
        """

        pkey = secrets.generate_private_key()
        pq = ProjectReq(
            name=name,
            private_key=pkey,
            description=desc,
            repository=repository,
        )
        r = self._http.post(
            f"/projects",
            json=asdict(pq),
        )
        created = False
        if r.status_code == 201:
            pd = ProjectData(**r.json())
            pc = ProjectCreated(pd=pd, private_key=pkey)
            if store_key:
                store_private_key(pkey, pd.projectid)
            return pc
        if r.status_code != 200:
            raise ProjectCreateError(name)
        return None

    def projects_get(self) -> Union[ProjectData, None]:
        breakpoint()
        r = self._http.get(f"/projects/{self.projectid}")
        if r.status_code == 200:
            return ProjectData(**r.json())
        return None

    def projects_list(self) -> List[ProjectData]:
        r = self._http.get(f"/projects")
        if r.status_code == 200:
            data = r.json()
            return [ProjectData(**d) for d in data]

    def projects_upload(self, zfile: ProjectZipFile):
        r = self._http.post(
            f"/projects/{self.projectid}/_upload?version={zfile.version}",
            content=binary_file_reader(zfile.filepath),
        )
        if r.status_code != 201 and r.status_code != 204:
            raise ProjectUploadError(self.projectid)

    def projects_build(self, version) -> Union[str, None]:
        rsp = self._http.post(f"/projects/{self.projectid}/_build?version={version}")
        if rsp.status_code == 202:
            return rsp.json()["execid"]
        return None

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

    def projects_private_key(self, store_key=False) -> Union[str, None]:
        """
        Gets private key to be shared to the docker container of a
        workflow task
        """
        r = self._http.get(f"/projects/{self.projectid}/_private_key")

        if r.status_code == 200:
            key = r.json()["private_key"]
            if store_key:
                store_private_key(key, self.projectid)
            return key
        return None

    def runtimes_get_all(self, lt=5) -> List[RuntimeVersionData]:
        data = self._http.get(f"/runtimes/{self.projectid}?lt={lt}")
        runtimes = [RuntimeVersionData(**dict_) for dict_ in data.json()]
        return runtimes

    def runtime_create(self, docker_name, version):
        rd = RuntimeVersionData(
            projectid=self.projectid, docker_name=docker_name, version=version
        )
        rsp = self._http.post(f"/runtimes/{self.projectid}", json=rd.dict())
        if rsp.status_code != 201 and rsp.status_code != 200:
            raise RuntimeCreationError(
                docker_name=docker_name, projectid=self.projectid
            )

    def runtime_delete(self, id):
        rsp = self._http.delete(f"/runtimes/{self.projectid}/{id}")
        if rsp.status_code != 200:
            raise RuntimeCreationError(docker_name=id, projectid=self.projectid)
