from nb_workflows.__version__ import __api_version__, __version__
from nb_workflows.client.base import BaseClient
from nb_workflows.shortcuts import client, secrets, settings
from nb_workflows.types import ClientSettings


def test_misc_version():

    assert isinstance(__version__, str)
    assert isinstance(__api_version__, str)


def test_misc_shortcuts():
    assert isinstance(settings, ClientSettings)
    assert isinstance(secrets, dict)
    assert isinstance(client, BaseClient)
