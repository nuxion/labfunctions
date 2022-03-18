import logging
from dataclasses import asdict
from typing import Callable, List, Optional

import httpx

from nb_workflows.conf import defaults
from nb_workflows.errors.client import LoginError, WorkflowStateNotSetError
from nb_workflows.types import NBTask, ProjectData, ScheduleData, SeqPipe, WorkflowData
from nb_workflows.types.client import WorkflowsFile
from nb_workflows.utils import open_yaml, write_yaml

from .state import WorkflowsState
from .types import Credentials
from .utils import store_credentials_disk


def get_http_client(**kwargs) -> httpx.Client:

    return httpx.Client(**kwargs)


class AuthFlow(httpx.Auth):
    requires_request_body = True
    requires_response_body = True

    def __init__(self, access_token, refresh_token, refresh_url):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.refresh_url = refresh_url

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        response = yield request

        # is_valid = validate_credentials_local(self.access_token)
        if response.status_code == 401:
            # If the server issues a 401 response, then issue a request to
            # refresh tokens, and resend the request.
            refresh_response = yield self.build_refresh_request()
            self.update_tokens(refresh_response)

            request.headers["Authorization"] = f"Bearer {self.access_token}"
            yield request

    def build_refresh_request(self):
        # Return an `httpx.Request` for refreshing tokens.
        rtkn = {"refresh_token": self.refresh_token}
        req = httpx.Request("POST", self.refresh_url, json=rtkn)
        req.headers["Authorization"] = f"Bearer {self.access_token}"
        return req

    def update_tokens(self, response):
        # Update the `.access_token` and `.refresh_token` tokens
        # based on a refresh response.
        data = response.json()
        self.access_token = data["access_token"]


class BaseClient:
    """
    A Generic client for API Server communication.


    By default, each client is associated to a specific project,
    this could be decoupled in the future because some actions
    like **startproject** are independent of the project.

    **Some conventions:**

    If a method calls to an API's endpoint, it should use the name
    of the endpoint at first. For instance:

        GET /workflows/<projectid>/<wfid>
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
        creds: Optional[Credentials] = None,
        wf_state: Optional[WorkflowsState] = None,
        version="0.1.0",
        http_init_func=get_http_client,
        timeout=defaults.CLIENT_TIMEOUT,
    ):

        self._addr = url_service
        self._creds = creds
        self._auth: Optional[AuthFlow] = None
        self.logger = logging.getLogger(__name__)
        self.state = wf_state
        self._version = version
        self._timeout = timeout
        self._http_creator = http_init_func
        self._http: httpx.Client = self._http_init()

    @property
    def http(self) -> httpx.Client:
        return self._http

    @property
    def projectid(self) -> str:
        if self.state:
            return self.state.projectid
        else:
            raise WorkflowStateNotSetError(__name__)

    @property
    def project_name(self) -> str:
        if self.state:
            return self.state.project_name
        else:
            raise WorkflowStateNotSetError(__name__)

    def _auth_init(self) -> AuthFlow:
        self._auth = AuthFlow(
            self._creds.access_token,
            self._creds.refresh_token,
            f"{self._addr}{defaults.REFRESH_TOKEN_PATH}",
        )

    def _http_init(self) -> httpx.Client:
        """When token is updated the client MUST BE updated too."""
        # _headers = {"Authorization": f"Bearer {self.creds.access_token}"}

        if self._creds and not self._auth:
            self._auth_init()
        return self._http_creator(
            base_url=self._addr, timeout=self._timeout, auth=self._auth
        )

    @property
    def creds(self) -> Credentials:
        return Credentials(
            access_token=self._auth.access_token,
            refresh_token=self._auth.refresh_token,
        )

    @creds.setter
    def creds(self, creds: Credentials):
        """
        If credentials are set, the http client should be
        re-initialized
        """
        self._creds = creds
        self._http = self._http_init()

    def login(self, u: str, p: str):
        rsp = httpx.post(
            f"{self._addr}/auth",
            json=dict(username=u, password=p),
            timeout=self._timeout,
        )
        if rsp.status_code == 200:
            self.creds = Credentials(**rsp.json())
            # self._http = self.http_init()
        else:
            raise LoginError(self._addr, u)

    def write(self, output="workflows.yaml"):
        self.state.write(output)

    def close(self):
        self._http.close()
