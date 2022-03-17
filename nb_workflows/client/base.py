from dataclasses import asdict
from typing import Callable, List, Optional

import httpx

from nb_workflows.conf import defaults
from nb_workflows.types import NBTask, ProjectData, ScheduleData, SeqPipe, WorkflowData
from nb_workflows.types.client import WorkflowsFile
from nb_workflows.utils import open_yaml, write_yaml

from .state import WorkflowsState
from .types import Credentials
from .utils import store_credentials_disk, validate_credentials_local


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

        is_valid = validate_credentials_local(self.access_token)
        if response.status_code == 401 or not is_valid:
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
        projectid: str,
        creds: Credentials,
        wf_state: Optional[WorkflowsState] = None,
        version="0.1.0",
        http_init_func=get_http_client,
        timeout=defaults.CLIENT_TIMEOUT,
    ):

        self.projectid = projectid
        self._addr = url_service

        self._auth = AuthFlow(
            creds.access_token,
            creds.refresh_token,
            f"{url_service}{defaults.REFRESH_TOKEN_PATH}",
        )

        self.state = wf_state
        self._version = version
        self._timeout = timeout
        self._http_creator = http_init_func
        self._http: httpx.Client = self._http_client_creator()

    def _http_client_creator(self) -> httpx.Client:
        """When token is updated the client MUST BE updated too."""
        # _headers = {"Authorization": f"Bearer {self.creds.access_token}"}
        return self._http_creator(
            base_url=self._addr, timeout=self._timeout, auth=self._auth
        )

    @property
    def creds(self) -> Credentials:
        return Credentials(
            access_token=self._auth.access_token,
            refresh_token=self._auth.refresh_token,
        )

    def write(self, output="workflows.yaml"):
        self.state.write(output)
