import os
from dataclasses import dataclass

import pytest
from libcloud.compute.base import Node, NodeLocation
from libcloud.compute.drivers.dummy import DummyNodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from pytest_mock import MockerFixture

from labfunctions.cluster.gcloud_provider import (
    GCEProvider,
    generic_zone,
    get_gce_driver,
)

from .factories import BlockStorageFactory


@dataclass
class VolumeMock:
    name: str


@pytest.fixture
def mock_driver(mocker):
    os.environ["LF_GCE_SERVICE_ACCOUNT"] = "test_account"
    os.environ["LF_GCE_PROJECT"] = "test_prj"

    Driver = mocker.Mock()
    mocker.patch(
        "labfunctions.cluster.gcloud_provider.get_gce_driver", return_value=Driver
    )
    yield Driver


def test_providers_gce_get_driver(mocker: MockerFixture):
    # mocker.patch("labfunctions.cluster.gcloud_provider.get_driver",
    #             return_value=DummyNodeDriver)

    D = get_gce_driver()
    assert D.ex_instancegroupmanager_set_instancetemplate


def test_providers_gce_generic_zone():
    d = get_driver("dummy")(creds="zara")

    z = generic_zone("home", d)
    assert isinstance(z, NodeLocation)


def test_providers_gce_init(mocker: MockerFixture, mock_driver):
    gp = GCEProvider()
    assert isinstance(gp, GCEProvider)
    assert gp.conf.service_account == "test_account"
    assert mock_driver.call_args[1]["project"] == "test_prj"


def test_providers_gce__get_volume(mocker: MockerFixture, mock_driver):
    vols = [VolumeMock(name="test"), VolumeMock(name="no match")]
    driver = mocker.MagicMock()
    driver.list_volumes.return_value = vols
    mock_driver.return_value = driver
    gp = GCEProvider()
    vol = gp._get_volume("test")
    non_vol = gp._get_volume("zzz")
    assert vol.name == "test"
    assert non_vol is None


def test_providers_gce_volumes_to_attach(mocker: MockerFixture, mock_driver):
    vols = [VolumeMock(name="test"), VolumeMock(name="no match")]
    driver = mocker.MagicMock()
    driver.list_volumes.return_value = vols
    driver.create_volume.return_value = vols[0]
    mock_driver.return_value = driver

    disk = BlockStorageFactory(name="test")
    disk2 = BlockStorageFactory(name="no-attach")
    gp = GCEProvider()
    volumes = gp._get_volumes_to_attach([disk, disk2])
    non_volumes = gp._get_volumes_to_attach([disk2])
    assert len(volumes) == 1
    assert volumes[0].name == vols[0].name
    assert non_volumes is None
