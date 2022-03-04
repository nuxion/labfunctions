from dataclasses import asdict
from typing import List, Optional

import httpx

from nb_workflows.core.entities import NBTask, ProjectData, ScheduleData, WorkflowData
from nb_workflows.utils import open_yaml, write_yaml

from .types import Credentials, WorkflowsFile
from .utils import store_credentials, validate_credentials_local


def get_http_client(**kwargs):
    return httpx.Client(**kwargs)


class AbstractClient:
    """Generic client to implement for different API endpoints
    Some conventions:
    - Methods that call to an API should use the name of the endpoint as the first
    parth of the method name.
    """

    def __init__(
        self,
        url_service: str,
        projectid: str,
        creds: Credentials,
        project: Optional[ProjectData] = None,
        workflows: Optional[List[NBTask]] = None,
        version="0.1.0",
    ):

        self.projectid = projectid
        self.creds = creds

        self._addr = url_service
        self._workflows = workflows
        self._project = project
        self._version = version
        _headers = {"Authorization": f"Bearer {creds.access_token}"}
        self._http = get_http_client(headers=_headers)

    @property
    def wf_file(self) -> WorkflowsFile:
        return WorkflowsFile(
            version=self._version,
            project=self._project,
            # workflows={w.alias: w for w in self._workflows}
            workflows=self._workflows,
        )

    def sync_file(self):

        wfs = self.workflows_list()
        tasks = []
        for w in wfs:
            task = NBTask(**w.job_detail)
            if w.job_detail.get("schedule"):
                task.schedule = ScheduleData(**w.job_detail["schedule"])
            tasks.append(task)

        self._workflows = tasks
        self.write()

    def auth_refresh(self):
        r = self._http.post(
            f"{self._addr}/auth/refresh",
            json={"refresh_token": self.creds.refresh_token},
        )
        data = r.json()
        self.creds.access_token = data["access_token"]
        store_credentials(self.creds)

    def auth_verify_or_refresh(self) -> bool:
        valid = validate_credentials_local(self.creds.access_token)
        if not valid:
            self.auth_refresh()
            return True
        return False

    def write(self, output="workflows.yaml"):

        wfs = [asdict(w) for w in self.wf_file.workflows]
        wf_ = self.wf_file.dict()
        wf_["workflows"] = wfs
        write_yaml("workflows.yaml", wf_)

    @staticmethod
    def read(filepath="workflows.yaml") -> WorkflowsFile:
        # data_dict = open_toml(filepath)
        data_dict = open_yaml(filepath)

        wf = WorkflowsFile(**data_dict)
        if wf.project:
            wf.project = ProjectData(**data_dict["project"])
        if wf.workflows:
            # _wfs = data_dict["workflows"]
            # wf.workflows = {_wfs[k]["alias"]: NBTask(**_wfs[k])
            #                for k in _wfs.keys()}
            wf.workflows = [NBTask(**w) for w in data_dict["workflows"]]
        return wf

    def workflows_list(self) -> List[WorkflowData]:
        self.auth_verify_or_refresh()
        r = self._http.get(f"{self._addr}/workflows/{self.projectid}")

        return [WorkflowData(**r) for r in r.json()["rows"]]
