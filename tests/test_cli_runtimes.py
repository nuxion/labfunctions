import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from labfunctions.cmd import runtimes
from labfunctions.conf.server_settings import settings


def test_cli_runtimes_main(mocker: MockerFixture):
    runner = CliRunner()
    result = runner.invoke(runtimes.runtimescli)

    assert result.exit_code == 0


def test_cli_runtimes_generate(mocker: MockerFixture, redis):
    runner = CliRunner()
    spy = mocker.patch(
        "labfunctions.cmd.runtimes.runtimes.generate_dockerfile", return_value=None
    )
    result = runner.invoke(
        runtimes.generate,
        ["--from-file", "tests/runtimes_test.yaml"],
    )
    assert result.exit_code == 0
