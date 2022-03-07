from dataclasses import asdict
from typing import Callable, List, Optional

import httpx

from nb_workflows.core.entities import NBTask, ProjectData, ScheduleData, WorkflowData
from nb_workflows.utils import open_yaml, write_yaml

from .types import Credentials, WorkflowsFile
from .utils import store_credentials_disk, validate_credentials_local


def get_http_client(**kwargs) -> httpx.Client:
    return httpx.Client(**kwargs)


class BaseClient:
    """
    A Generic client for API Server communication.


    By default, each client is associated to a specific project,
    this could be decoupled in the future because some actions
    like **startproject** are independent of the project.

    **Some conventions:**

    If a method calls to an API's endpoint, it should use the name
    of the endpoint at first. For instance:

        GET /workflows/<projectid>/<jobid>
    The method name for that endpoint could be: `workflows_get_one()`


    :param url_service: base url of the WORKFLOWS_SERVICE
    :param projectid: projectid realted to ProjectsModel
    :param creds: Credentials type, it includes access_token and refresh_token
    :param store_creds: Optional, if true the credentials will be stored on disk
    :param project: Optional[Project] type
    :param version: version api, not implemented yet
    :param http_init_func: Callable, a function which initializes
    a HTTPX client.
    """

    def __init__(
        self,
        url_service: str,
        projectid: str,
        creds: Credentials,
        store_creds=False,
        project: Optional[ProjectData] = None,
        workflows: Optional[List[NBTask]] = None,
        version="0.1.0",
        http_init_func=get_http_client,
    ):

        self.projectid = projectid
        self.creds: Credentials = creds
        self._store_creds = store_creds

        self._addr = url_service
        self._workflows: Optional[List[NBTask]] = workflows
        self._project = project
        self._version = version
        self._http_creator = http_init_func
        self._http: httpx.Client = self._http_client_creator()
        self.auth_verify_or_refresh()

    def _http_client_creator(self) -> httpx.Client:
        """When token is updated the client MUST BE updated too."""

        _headers = {"Authorization": f"Bearer {self.creds.access_token}"}
        return self._http_creator(headers=_headers)

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

    def store_credentials(self):
        store_credentials_disk(self.creds)

    def auth_refresh(self):
        """If the access_token is expired, it should be updated using
        the refres_token. After that http client must be re-initialized
        and new credentials are stored.

        """
        r = self._http.post(
            f"{self._addr}/auth/refresh",
            json={"refresh_token": self.creds.refresh_token},
        )
        data = r.json()
        self.creds.access_token = data["access_token"]
        self._http_client_creator()
        if self._store_creds:
            self.store_credentials()

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
