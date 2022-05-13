import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

from labfunctions import defaults, errors, secrets, types
from labfunctions.errors.client import ProjectCreateError, ProjectUploadError
from labfunctions.errors.runtimes import RuntimeCreationError
from labfunctions.utils import binary_file_reader, parse_var_line

from .base import BaseClient
from .utils import store_private_key


class ProjectsClient(BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def projects_create(
        self,
        name: str,
        desc: Optional[str] = None,
        repository: Optional[str] = None,
        store_key: bool = True,
    ) -> Union[types.projects.ProjectCreated, None]:
        """
        A staless project creator it don't use any internal state of the client
        instead, all values should be provided in this method for a project to be
        created
        """

        pkey = secrets.generate_private_key()
        pq = types.ProjectReq(
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
            pd = types.ProjectData(**r.json())
            pc = types.projects.ProjectCreated(pd=pd, private_key=pkey)
            if store_key:
                store_private_key(pkey, self.working_area)
            return pc
        if r.status_code != 200:
            raise ProjectCreateError(name)
        return None

    def projects_get(self) -> Union[types.ProjectData, None]:
        r = self._http.get(f"/projects/{self.projectid}")
        if r.status_code == 200:
            return types.ProjectData(**r.json())
        return None

    def projects_list(self) -> List[types.ProjectData]:
        r = self._http.get(f"/projects")
        if r.status_code == 200:
            data = r.json()
            return [types.ProjectData(**d) for d in data]
        return []

    def projects_upload(self, zfile: types.ProjectBundleFile):
        url = (
            f"/projects/{self.projectid}"
            f"/_upload?runtime={zfile.runtime_name}&version={zfile.version}"
        )

        r = self._http.post(
            url,
            content=binary_file_reader(zfile.filepath),
        )
        if r.status_code != 201 and r.status_code != 204:
            raise ProjectUploadError(self.projectid)

    def projects_build(self, spec: types.RuntimeSpec, version: str) -> Union[str, None]:
        rsp = self._http.post(
            f"/projects/{self.projectid}/_build?version={version}", json=spec.dict()
        )
        if rsp.status_code == 202:
            return rsp.json()["execid"]
        return None

    def projects_create_agent(self) -> Union[str, None]:
        r = self._http.post(f"/projects/{self.projectid}/agent")

        if r.status_code == 201:
            return r.json()["msg"]

        return None

    def projects_agent_token(
        self, agentname: Optional[str] = None, projectid: Optional[str] = None
    ) -> Union[types.user.AgentJWTResponse, None]:
        """
        If an agentname is given then it will ask for that agent, if not, then it will
        get the token for the last agent created for this project.
        """
        prj = self.projectid
        if projectid:
            prj = projectid

        url = f"/projects/{prj}/agent/_token"
        if agentname:
            url = f"/projects/{prj}/agent/{agentname}/_token"

        r = self._http.post(url)

        if r.status_code == 200:
            return types.user.AgentJWTResponse(**r.json())

        return None

    def projects_agent_list(self) -> List[str]:
        """
        If an agentname is given then it will ask for that agent, if not, then it will
        get the token for the last agent created for this project.
        """

        url = f"/projects/{self.projectid}/agent"
        r = self._http.get(url)

        if r.status_code == 200:
            return r.json()
        return []

    def project_agent_delete(self, agentname) -> bool:

        url = f"/projects/{self.projectid}/agent/{agentname}"
        r = self._http.delete(url)
        if r.status_code == 200:
            return True
        return False

    def projects_private_key(
        self, projectid: Optional[str] = None, store_key=False
    ) -> Union[str, None]:
        """
        Gets private key to be shared to the docker container of a
        workflow task
        """
        projectid = projectid or self.projectid
        url = f"/projects/{projectid}/_private_key"
        r = self._http.get(url)

        if r.status_code == 200:
            key = r.json().get("private_key")
            if not key:
                raise errors.PrivateKeyNotFound(self.projectid)
            if store_key:
                store_private_key(key, projectid)
            return key
        raise errors.PrivateKeyNotFound(projectid)
        return None

    def runtimes_get_all(self, lt=5) -> List[types.RuntimeData]:
        data = self._http.get(f"/runtimes/{self.projectid}?lt={lt}")
        runtimes = [types.RuntimeData(**dict_) for dict_ in data.json()]
        return runtimes

    def runtime_create(self, req: types.RuntimeReq):

        rsp = self._http.post(f"/runtimes/{self.projectid}", json=req.dict())
        if rsp.status_code != 201 and rsp.status_code != 200:
            raise RuntimeCreationError(
                docker_name=req.docker_name, projectid=self.projectid
            )

    def runtime_delete(self, rid):
        rsp = self._http.delete(f"/runtimes/{self.projectid}/{rid}")
        if rsp.status_code != 200:
            raise RuntimeCreationError(docker_name=rid, projectid=self.projectid)
