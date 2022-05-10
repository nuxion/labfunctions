import shutil
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nb_workflows.client.nbclient import NBClient
from nb_workflows.conf.server_settings import settings
from nb_workflows.io.kvspec import GenericKVSpec
from nb_workflows.runtimes import builder

from .factories import BuildCtxFactory, DockerBuildLogFactory, ProjectDataFactory

# spy = mocker.spy(builder, "docker_build")


@pytest.fixture
def kvstore() -> GenericKVSpec:
    kv = GenericKVSpec.create("nb_workflows.io.kv_local.KVLocal", "nbworkflows")
    return kv


def test_builder_unzip_runtime(mocker: MockerFixture, tempdir):
    settings.BASE_PATH = tempdir
    shutil.make_archive(
        f"{tempdir}/testzip", format="zip", root_dir="nb_workflows/runtimes"
    )
    builder.unzip_runtime(f"{tempdir}/testzip.zip", tempdir)

    is_file = Path(f"{tempdir}/__init__.py").is_file()

    assert is_file


def test_builder_BuildTask(mocker: MockerFixture, kvstore):
    client = NBClient(url_service="http://localhost:8000")
    mock = mocker.patch(
        "nb_workflows.runtimes.builder.client.agent", return_value=client
    )

    task = builder.BuildTask("test", kvstore=kvstore, nbclient=client)
    task2 = builder.BuildTask("test", kvstore=kvstore)

    assert isinstance(task.client, NBClient)
    assert task2.client._addr == "http://localhost:8000"
    assert mock.called


def test_builder_BuildTask_get_runtime(mocker: MockerFixture, kvstore, tempdir):
    def stream_data(any_):
        for x in range(5):
            yield str(x).encode()

    mock = mocker.MagicMock()
    mock.get_stream.return_value = [str(x).encode() for x in range(6)]
    # mock.get_stream = stream_data
    client = NBClient(url_service="http://localhost:8000")
    task = builder.BuildTask("test", kvstore=kvstore, nbclient=client)
    task.kv = mock
    task.get_runtime_file(f"{tempdir}/test.zip", "dowload_zip_url")
    is_file = Path(f"{tempdir}/test.zip").is_file()
    assert is_file
    assert mock.get_stream.called


def test_builder_BuildTask_run(mocker: MockerFixture, kvstore, tempdir):

    client = NBClient(url_service="http://localhost:8000")
    ctx = BuildCtxFactory()

    log = DockerBuildLogFactory(error=True)
    unzip = mocker.patch(
        "nb_workflows.runtimes.builder.unzip_runtime", return_value=None
    )
    get_runtime = mocker.patch(
        "nb_workflows.runtimes.builder.BuildTask.get_runtime_file", return_value=None
    )
    cmd = mocker.patch(
        "nb_workflows.runtimes.builder.DockerCommand.build", return_value=log
    )

    task = builder.BuildTask("test", kvstore=kvstore, nbclient=client)
    log_run = task.run(ctx)
    assert unzip.called
    assert get_runtime.called
    assert cmd.called
    assert log_run.error
    assert cmd.call_args_list[0][1]["tag"] == "nbworkflows/test"


def test_builder_BuildTask_run_repo(mocker: MockerFixture, kvstore, tempdir):

    client = NBClient(url_service="http://localhost:8000")
    ctx = BuildCtxFactory(registry="testregistry")

    log = DockerBuildLogFactory(error=True)
    unzip = mocker.patch(
        "nb_workflows.runtimes.builder.unzip_runtime", return_value=None
    )
    get_runtime = mocker.patch(
        "nb_workflows.runtimes.builder.BuildTask.get_runtime_file", return_value=None
    )
    cmd = mocker.patch(
        "nb_workflows.runtimes.builder.DockerCommand.build", return_value=log
    )

    task = builder.BuildTask("test", kvstore=kvstore, nbclient=client)
    log_run = task.run(ctx)
    assert unzip.called
    assert get_runtime.called
    assert cmd.called
    assert log_run.error
    assert cmd.call_args_list[0][1]["tag"] == "testregistry/nbworkflows/test"


def test_builder_exec(mocker: MockerFixture, kvstore):
    agent_mock = mocker.MagicMock()
    build_mock = mocker.MagicMock()

    ctx = BuildCtxFactory()
    log = DockerBuildLogFactory()
    # spy = mocker.spy(builder, "BuildTask")
    # task_mock = mocker.patch(
    #    "nb_workflows.runtimes.builder.BuildTask", return_value=build_mock
    # )
    task_mock = mocker.patch(
        "nb_workflows.runtimes.builder.BuildTask.run", return_value=log
    )
    agent = mocker.patch(
        "nb_workflows.runtimes.builder.client.agent", return_value=agent_mock
    )
    task_mock.run.return_value = mocker.Mock(return_value=log)

    result = builder.builder_exec(ctx)

    assert id(result) == id(log)
    # assert task_mock.call_args_list[0][0][0] == ctx.projectid
    assert result.error is False
    assert agent.call_args_list[0][1]["url_service"] == "http://localhost:8000"
