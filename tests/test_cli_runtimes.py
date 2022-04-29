import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from nb_workflows.cmd import runtimes
from nb_workflows.conf.server_settings import settings


def test_cli_runtimes_main(mocker: MockerFixture):
    runner = CliRunner()
    result = runner.invoke(runtimes.runtimescli)

    assert result.exit_code == 0


def test_cli_runtimes_machine_create(mocker: MockerFixture, redis):
    runner = CliRunner()
    spy = mocker.patch(
        "nb_workflows.cmd.runtimes.generate_dockerfile", return_value=None
    )
    result = runner.invoke(
        runtimes.generate,
        ["--from-file", "tests/runtimes_test.yaml"],
    )
    assert result.exit_code == 0
