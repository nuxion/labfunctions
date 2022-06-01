import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Union

import httpx
import jwt

from labfunctions import defaults, errors, log, types
from labfunctions.client.labstate import LabState
from labfunctions.client.utils import get_credentials_disk
from labfunctions.events import EventManager
from labfunctions.hashes import generate_random
from labfunctions.utils import mkdir_p, open_yaml, write_yaml


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
        tkn = data.get("access_token")
        if not tkn:
            raise errors.AuthValidationFailed()
        self.access_token = tkn


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
    :param creds: TokenCreds type, it includes access_token and refresh_token
    :param store_creds: Optional, if true the credentials will be stored on disk
    :param project: Optional[Project] type
    :param version: version api, not implemented yet
    :param http_init_func: Callable, a function which initializes
    a HTTPX client.
    """

    def __init__(
        self,
        url_service: str,
        creds: Optional[types.TokenCreds] = None,
        lab_state: Optional[LabState] = None,
        version=defaults.API_VERSION,
        http_init_func=get_http_client,
        timeout=defaults.CLIENT_TIMEOUT,
        base_path: Optional[str] = None,
    ):
        self._addr = url_service
        self._creds = creds
        self._auth: Optional[AuthFlow] = None
        self.logger = log.client_logger
        self.state = lab_state
        self._version = version
        self._timeout = timeout
        self._http_creator = http_init_func
        self._http: httpx.Client = self._http_init()
        self.base_path = base_path
        self._home = Path.home() / defaults.CLIENT_HOME_DIR

    @property
    def working_area(self) -> Path:
        """Working area is used to store related project data as private keys
        temp build generation files and so on"""

        return self._home / self.projectid

    @property
    def homedir(self) -> Path:
        return self._home

    def create_homedir(self) -> Path:
        if not self._home.is_dir():
            mkdir_p(self._home)
            self._home.chmod(0o700)
        return self._home

    def info(self) -> Dict[str, Any]:
        workflows = None
        if self.state.workflows:
            workflows = list(self.state.workflows.keys())

        return {
            "projectid": self.projectid,
            "project_name": self.project_name,
            "workflows_service": self._addr,
            "homedir": str(self.homedir),
            "working_area": str(self.working_area),
            "file": self.state.filepath,
            "workflows": workflows,
            "user": self.user,
            "base_path": self.base_path,
        }

    @property
    def http(self) -> httpx.Client:
        return self._http

    @property
    def projectid(self) -> str:
        if self.state:
            return self.state.projectid
        else:
            raise errors.client.WorkflowStateNotSetError(__name__)

    @property
    def project_name(self) -> str:
        if self.state:
            return self.state.project_name
        else:
            raise errors.client.WorkflowStateNotSetError(__name__)

    # def get_context(self, execid=None) -> ExecutionNBTask:
    #    _env = os.getenv(defaults.EXECUTIONTASK_VAR)
    #    if _env:
    #        ctx = ExecutionNBTask(**json.loads(_env))
    #    else:
    #        ctx = context.create_dummy_ctx(self.projectid, execid)
    #    return ctx

    def _auth_init(self) -> AuthFlow:
        self._auth = AuthFlow(
            self._creds.access_token,
            self._creds.refresh_token,
            f"{self._addr}/{self._version}/{defaults.REFRESH_TOKEN_PATH}",
        )

    def _http_init(self) -> httpx.Client:
        """When token is updated the client MUST BE updated too."""
        # _headers = {"Authorization": f"Bearer {self.creds.access_token}"}

        if self._creds:
            self._auth_init()
        return self._http_creator(
            base_url=f"{self._addr}/{self._version}",
            timeout=self._timeout,
            auth=self._auth,
        )

    @property
    def user(self) -> Union[str, None]:
        if self._creds:
            decoded = jwt.decode(
                self._creds.access_token, options={"verify_signature": False}
            )

            return decoded["usr"]
        return None

    @property
    def creds(self) -> types.TokenCreds:
        return types.TokenCreds(
            access_token=self._auth.access_token,
            refresh_token=self._auth.refresh_token,
        )

    @creds.setter
    def creds(self, creds: types.TokenCreds):
        """
        If credentials are set, the http client should be
        re-initialized
        """
        self._creds = creds
        self._http = self._http_init()

    def load_creds(self):
        at = os.getenv(defaults.AGENT_TOKEN_ENV)
        rt = os.getenv(defaults.AGENT_REFRESH_ENV)
        if at and rt:
            self.creds = types.TokenCreds(access_token=at, refresh_token=rt)
        self.creds = get_credentials_disk(self.homedir)

    def login(self, u: str, p: str):
        rsp = httpx.post(
            f"{self._addr}/{self._version}/auth/login",
            json=dict(username=u, password=p),
            timeout=self._timeout,
        )
        if rsp.status_code == 200:
            self.creds = types.TokenCreds(**rsp.json())
            # self._http = self.http_init()
        else:
            raise errors.client.LoginError(self._addr, u)

    def verify(self):
        try:
            rsp = self._http.get(f"/auth/verify")
            if rsp.status_code == 200:
                return True
        except errors.AuthValidationFailed:
            self._creds = None
            self._auth = None
            return False

    def write(self, output=defaults.LABFILE_NAME):
        self.state.write(output)

    def close(self):
        self._http.close()

    def events_listen(
        self, execid, last=None, timeout=None
    ) -> Generator[types.events.EventSSE, None, None]:
        timeout = timeout or self._timeout
        # uri = f"/events/{self.projectid}/{execid}/_listen"
        uri = f"{self._addr}/{self._version}/events/{self.projectid}/{execid}/_listen"
        if last:
            uri = f"{uri}?last={last}"

        headers = {"Authorization": f"Bearer {self.creds.access_token}"}

        with httpx.stream("GET", uri, timeout=timeout, headers=headers) as r:
            buffer_ = ""
            for line in r.iter_lines():
                buffer_ += line
                if buffer_.endswith("\n\n"):
                    evt = EventManager.from_sse2event(buffer_)
                    # print(evt.dict())
                    if evt.data == "exit":
                        return
                    yield evt
                    buffer_ = ""

    def events_publish(self, execid, data, event=None):
        final = data
        if isinstance(data, dict):
            final = json.dumps(data)
        if final:
            evt = types.events.EventSSE(data=final, event=event)
            self._http.post(
                f"/events/{self.projectid}/{execid}/_publish", json=evt.dict()
            )
        else:
            self.logger.warning(f"execid: {execid} empty message")
