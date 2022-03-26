import json

from pytest_mock import MockerFixture

from nb_workflows.client import diskclient as dc
from nb_workflows.client import shortcuts, utils
from nb_workflows.client.base import AuthFlow
from nb_workflows.client.diskclient import DiskClient
from nb_workflows.client.types import Credentials

from .factories import credentials_generator


class MockLoginRsp:
    status_code = 200

    @staticmethod
    def json():
        return dict(access_token="token_test", refresh_token="refresh")


class MockPrivKeyRsp:
    status_code = 200

    @staticmethod
    def json():
        return dict(private_key="test_key")


def test_client_diskclient_mro():
    """https://stackoverflow.com/questions/3277367/how-does-pythons-super-work-with-multiple-inheritance"""

    first = str(DiskClient.__mro__[0])
    last = str(DiskClient.__mro__[-2])

    assert "DiskClient" in first
    assert "BaseClient" in last


def test_client_diskclient_params():
    with open("tests/workflow.ipynb", "r", encoding="utf-8") as f:
        nb_dict = json.loads(f.read())

    params = dc.get_params_from_nb(nb_dict)
    assert params.get("WFID") == "test_job"
    assert len(params.keys()) == 5


def test_client_diskclient_notebook_tmp(tempdir):
    dc.DiskClient.notebook_template(f"{tempdir}/test.ipynb")
    dict_ = dc.open_notebook(f"{tempdir}/test.ipynb")
    params = dc.get_params_from_nb(dict_)

    assert params.get("WFID") == "test_job"
    assert len(params.keys()) == 5


# def test_client_diskclient_from_file(mocker: MockerFixture, auth_helper):
def test_client_diskclient_from_file(monkeypatch, auth_helper):
    def mock_creds(*args, **kwargs):
        creds = credentials_generator(auth_helper)
        return creds

    monkeypatch.setattr(
        "nb_workflows.client.diskclient.get_credentials_disk", mock_creds
    )
    client = shortcuts.from_file(
        "tests/workflows_test.yaml", "http://localhost:8000", ".test"
    )

    assert client._addr == "http://localhost:8000"
    assert isinstance(client, DiskClient)


def test_client_diskclient_from_file_none(monkeypatch, auth_helper):
    def mock_login(*args, **kwargs):
        creds = credentials_generator(auth_helper)
        return creds

    def mock_creds(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "nb_workflows.client.diskclient.get_credentials_disk", mock_creds
    )
    monkeypatch.setattr(DiskClient, "logincli", mock_login)

    # mocker.patch(
    #     "nb_workflows.client.utils.get_credentials_disk", return_value=5)
    client = shortcuts.from_file(
        "tests/workflows_test.yaml", "http://localhost:8000", ".test"
    )

    assert client._addr == "http://localhost:8000"
    assert isinstance(client, DiskClient)


def test_client_diskclient_login(monkeypatch, tempdir):
    import httpx

    def mock_post(*args, **kwargs):
        return MockLoginRsp()

    monkeypatch.setattr(httpx, "post", mock_post)

    c = DiskClient(url_service="http://localhost:8000")
    # c.creds = Credentials(access_token="test_token", refresh_token="refresh")
    c.login("test", "test_pass", home_dir=tempdir)

    with open(f"{tempdir}/credentials.json", "r") as f:
        data = json.loads(f.read())

    assert data["access_token"] == "token_test"
    assert c._creds.access_token == "token_test"
    assert c._creds.refresh_token == "refresh"
    assert isinstance(c._http.auth, AuthFlow)


def test_client_diskclient_logincli(mocker: MockerFixture):
    import httpx

    mocker.patch(
        "nb_workflows.client.diskclient.get_credentials_disk", return_value=None
    )

    mocker.patch("nb_workflows.client.diskclient.input", return_value="nuxion")

    mocker.patch(
        "nb_workflows.client.diskclient.getpass.getpass", return_value="nuxion"
    )

    mocker.patch("nb_workflows.client.diskclient.DiskClient.login", return_value=None)

    c = DiskClient(url_service="http://localhost:8000")
    c.logincli()


def test_client_diskclient_priv_key(mocker, monkeypatch, tempdir):
    import httpx

    def mock_get(*args, **kwargs):
        return MockPrivKeyRsp()

    mocker.patch("nb_workflows.client.diskclient.store_private_key", return_value=None)

    mocker.patch(
        "nb_workflows.client.diskclient.DiskClient.projectid", return_value="test"
    )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    c = DiskClient(url_service="http://localhost:8000")
    key = c.projects_private_key()
    assert key == "test_key"
