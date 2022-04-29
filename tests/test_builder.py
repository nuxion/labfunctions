from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nb_workflows.conf.server_settings import settings
from nb_workflows.executors import builder

from .factories import BuildCtxFactory, ProjectDataFactory


def test_builder_prepare_files(mocker: MockerFixture, tempdir):
    settings.BASE_PATH = tempdir

    mocker.patch(
        "nb_workflows.executors.builder._download_zip_project", return_value=None
    )

    mocker.patch("nb_workflows.executors.builder._extract_project", return_value=None)

    ctx = BuildCtxFactory()
    prj_dir, temp_dir = builder.prepare_files(ctx)

    assert str(prj_dir).endswith(f"{ctx.projectid}/build")
    assert str(temp_dir).endswith("build/tmp")


def test_builder_exec(mocker: MockerFixture, tempdir):
    client_mock = mocker.MagicMock()

    pd = ProjectDataFactory()
    client_mock.projects_get.return_value = pd
    client_mock.events_publish.return_vlaue = None

    # mock_docker_build = mocker.create_autospec(builder.docker_build, return_value="logs")

    prj_dir = Path(f"{tempdir}/build")
    tmp = prj_dir / "tmp"

    mocker.patch(
        "nb_workflows.executors.builder.client.agent", return_value=client_mock
    )

    mocker.patch(
        "nb_workflows.executors.builder.prepare_files", return_value=(prj_dir, tmp)
    )

    mocker.patch("nb_workflows.executors.builder.docker_build", return_value="logs")
    spy = mocker.spy(builder, "docker_build")

    ctx = BuildCtxFactory()

    logs = builder.builder_exec(ctx)
    dir_ = spy.call_args[0][0]
    push = spy.call_args[1]["push"]
    assert logs == "logs"
    assert f"{tmp}/src" == dir_
    assert push is not True


def test_builder_exec_repo(mocker: MockerFixture, tempdir):
    client_mock = mocker.MagicMock()

    pd = ProjectDataFactory()
    client_mock.projects_get.return_value = pd
    client_mock.events_publish.return_vlaue = None
    settings.DOCKER_REGISTRY = "test:5000"

    # mock_docker_build = mocker.create_autospec(builder.docker_build, return_value="logs")

    prj_dir = Path(f"{tempdir}/build")
    tmp = prj_dir / "tmp"

    mocker.patch(
        "nb_workflows.executors.builder.client.agent", return_value=client_mock
    )

    mocker.patch(
        "nb_workflows.executors.builder.prepare_files", return_value=(prj_dir, tmp)
    )

    mocker.patch("nb_workflows.executors.builder.docker_build", return_value="logs")
    spy = mocker.spy(builder, "docker_build")

    ctx = BuildCtxFactory()

    logs = builder.builder_exec(ctx)
    dir_ = spy.call_args[0][0]
    push = spy.call_args[1]["push"]
    assert logs == "logs"
    assert f"{tmp}/src" == dir_
    assert push
