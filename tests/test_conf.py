import os
from unittest import mock

from pytest_mock import MockerFixture

from labfunctions import defaults
from labfunctions.types import ClientSettings


@mock.patch.dict(os.environ, {defaults.SERVICE_URL_ENV: "https://localhost"})
def test_conf_define_url_service_env(mocker: MockerFixture):
    # mocker.patch("labfunctions.conf.utils.os.environ.get",)
    from labfunctions.conf import utils

    dict_mock = {"WORKFLOW_SERVICE": "http://127.0.0.1:8000"}
    url = utils.define_url_service(dict_mock)
    assert url == "https://localhost"


@mock.patch.dict(os.environ, {defaults.SERVICE_URL_ENV: ""})
def test_conf_define_url_service_settings(mocker: MockerFixture):
    # mocker.patch("labfunctions.conf.utils.os.environ.get",)
    from labfunctions.conf import utils

    dict_mock = {"WORKFLOW_SERVICE": "http://127.0.0.1:8000"}
    url = utils.define_url_service(dict_mock)
    assert url == "http://127.0.0.1:8000"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: "/tmp"})
def test_conf_define_base_env(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = "/tmp"
    from labfunctions.conf import utils

    def mock_execute(*args, **kwargs):
        raise AttributeError()

    monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    base = utils.define_base_path()
    assert base == "/tmp"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: ""})
def test_conf_define_base_git(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from labfunctions.conf import utils

    def mock_execute(*args, **kwargs):
        return "/from_git"

    monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    base = utils.define_base_path()
    assert base == "/from_git"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: ""})
def test_conf_define_base_parent(tempdir, mocker: MockerFixture):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from labfunctions.conf import utils

    mocker.patch("labfunctions.conf.utils.os.getcwd", return_value="/tmp/test")
    mocker.patch("labfunctions.conf.utils.execute_cmd", side_effect=[IndexError()])

    base = utils.define_base_path()
    assert base == "/tmp/test"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: os.getcwd()})
def test_conf_load_client(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from labfunctions.conf import utils

    os.environ[defaults.SERVICE_URL_ENV] = "https://localhost"

    # def mock_execute(*args, **kwargs):
    #   return ""
    # monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    settings = utils.load_client(settings_module="tests.settings_test")

    assert isinstance(settings, ClientSettings)
    assert settings.SETTINGS_MODULE == "tests.settings_test"
    assert settings.WORKFLOW_SERVICE == "https://localhost"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: os.getcwd()})
def test_conf_load_client_default(monkeypatch):
    from labfunctions.conf import utils

    settings = utils.load_client()

    assert isinstance(settings, ClientSettings)
    assert settings.SETTINGS_MODULE == utils.GLOBAL_CLIENT
