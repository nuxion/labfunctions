import os
from unittest import mock

from nb_workflows import defaults
from nb_workflows.types import ClientSettings


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: "/tmp"})
def test_conf_define_base_env(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = "/tmp"
    from nb_workflows.conf import utils

    def mock_execute(*args, **kwargs):
        raise AttributeError()

    monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    base = utils.define_base_path()
    assert base == "/tmp"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: ""})
def test_conf_define_base_git(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from nb_workflows.conf import utils

    def mock_execute(*args, **kwargs):
        return "/from_git"

    monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    base = utils.define_base_path()
    assert base == "/from_git"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: ""})
def test_conf_define_base_parent(monkeypatch, tempdir):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from nb_workflows.conf import utils

    def mock_execute(*args, **kwargs):
        raise AttributeError()

    def mock_pwd(*args, **kwargs):
        return tempdir

    monkeypatch.setattr(utils, "execute_cmd", mock_execute)
    monkeypatch.setattr(os, "getcwd", mock_pwd)
    base = utils.define_base_path()
    assert base == "/tmp"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: os.getcwd()})
def test_conf_load_client(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from nb_workflows.conf import utils

    # def mock_execute(*args, **kwargs):
    #   return ""
    # monkeypatch.setattr(utils, "execute_cmd", mock_execute)

    settings = utils.load_client(settings_module="tests.settings_test")

    assert isinstance(settings, ClientSettings)
    assert settings.SETTINGS_MODULE == "tests.settings_test"


@mock.patch.dict(os.environ, {defaults.BASE_PATH_ENV: os.getcwd()})
def test_conf_load_client_default(monkeypatch):
    # os.environ[defaults.BASE_PATH_ENV] = None
    from nb_workflows.conf import utils

    # def mock_execute(*args, **kwargs):
    #   return ""
    # monkeypatch.setattr(utils, "execute_cmd", mock_execute)

    settings = utils.load_client()

    assert isinstance(settings, ClientSettings)
    assert settings.SETTINGS_MODULE == utils.GLOBAL_CLIENT
