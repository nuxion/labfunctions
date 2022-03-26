import httpx
import pytest

from nb_workflows.client.base import AuthFlow, BaseClient
from nb_workflows.client.types import Credentials
from nb_workflows.errors import LoginError
from nb_workflows.errors.client import LoginError, WorkflowStateNotSetError

url = "http://localhost:8000"


class MockLoginRsp:
    status_code = 200

    @staticmethod
    def json():
        return dict(access_token="token_test", refresh_token="refresh")


class MockLoginErrorRsp:
    status_code = 401

    @staticmethod
    def json():
        return dict(msg="error")


def test_client_base_auth():
    au = AuthFlow(
        access_token="test", refresh_token="test", refresh_url="http://localhost;8000"
    )
    req = au.build_refresh_request()

    mock_req = httpx.Request("http://localhost:8000/test", "GET")

    rsp = au.auth_flow(mock_req)
    rsp.send(None)
    authorized_req = rsp.send(httpx.Response(status_code=401))

    assert req.headers["Authorization"] == "Bearer test"
    assert isinstance(req, httpx.Request)
    assert authorized_req.headers["Authorization"]


def test_client_base_init():

    bc = BaseClient(url_service=url)
    assert isinstance(bc, BaseClient)
    assert isinstance(bc._http, httpx.Client)
    assert not bc._auth


def test_client_base_init_creds(monkeypatch):
    def mock_close(*args, **kwargs):
        return True

    monkeypatch.setattr(httpx.Client, "close", mock_close)
    creds = Credentials(access_token="test_token", refresh_token="refresh")
    bc = BaseClient(url_service=url, creds=creds)

    with pytest.raises(WorkflowStateNotSetError):
        bc.projectid

    with pytest.raises(WorkflowStateNotSetError):
        bc.project_name

    bc.close()

    assert isinstance(bc.http, httpx.Client)
    assert isinstance(bc._http, httpx.Client)
    assert isinstance(bc._auth, AuthFlow)
    assert bc.creds.access_token == creds.access_token


def test_client_base_login(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockLoginRsp()

    monkeypatch.setattr(httpx, "post", mock_post)

    bc = BaseClient(url_service=url)
    bc.login(u="test", p="testing_password")

    assert bc.creds.access_token == "token_test"


def test_client_base_login_error(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockLoginErrorRsp()

    monkeypatch.setattr(httpx, "post", mock_post)

    bc = BaseClient(url_service=url)
    with pytest.raises(LoginError):
        bc.login(u="test", p="testing_password")
