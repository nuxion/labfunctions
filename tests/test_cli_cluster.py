import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from labfunctions.cluster.context import create_machine_ctx, machine_from_settings
from labfunctions.cmd import cluster
from labfunctions.conf.server_settings import settings
from labfunctions.errors.cluster import ClusterSpecNotFound

from .factories import MachineInstanceFactory


def test_cli_cluster_main(mocker: MockerFixture):
    runner = CliRunner()
    result = runner.invoke(cluster.clustercli)

    assert result.exit_code == 0


def test_cli_cluster_machine_create(mocker: MockerFixture, redis):
    runner = CliRunner()
    m = MachineInstanceFactory()

    cc_mock = mocker.MagicMock()
    cc_mock.create_instance.return_value = m

    result = runner.invoke(
        cluster.create_machinecli,
        ["--from-file", "tests/clusters_test.yaml", "-C", "local"],
    )
    assert result.exit_code == 0


def test_cli_cluster_machine_create_error(mocker: MockerFixture, redis):
    runner = CliRunner()
    result = runner.invoke(
        cluster.create_machinecli,
        ["--from-file", "tests/clusters_test.yaml", "-C", "non-exist"],
    )
    assert result.exit_code == -1


def test_cli_cluster_machine_destroy(mocker: MockerFixture, redis):
    runner = CliRunner()
    spy = mocker.patch(
        "labfunctions.cluster.control.ClusterControl.destroy_instance",
        return_value=None,
    )

    result = runner.invoke(
        cluster.destroy_machinecli,
        ["--from-file", "tests/clusters_test.yaml", "-C", "local", "test"],
    )
    assert result.exit_code == 0
    assert spy.call_count == 1


def test_cli_cluster_catalog(mocker: MockerFixture):
    runner = CliRunner()
    result = runner.invoke(cluster.catalogcli)
    result2 = runner.invoke(cluster.catalogcli, ["-p", "gce"])
    assert result.exit_code == 0
    assert result2.exit_code == 0
    assert "e2-micro" in result2.stdout
