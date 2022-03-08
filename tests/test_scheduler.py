import pickle
from unittest import mock

from pytest_mock import MockerFixture

from nb_workflows.scheduler import SchedulerExecutor

from .resources import nb_task_schedule, nb_task_simple, schedule_data, wd


def test_scheduler_instance(redis):

    s = SchedulerExecutor(redis, qname="test", is_async=False)
    assert isinstance(s, SchedulerExecutor)


# @mock.patch('nb_workflows.executors.docker.docker_exec', return_value=3)
def test_scheduler_enqueue_docker(mocker: MockerFixture, redis):
    from nb_workflows.executors.docker import docker_exec

    # mocker.patch("nb_workflows.scheduler.docker_exec", return_value=5)

    nb_client = mocker.MagicMock()
    docker_client = mocker.MagicMock()

    docker_client.containers.run.return_value = "OK"
    nb_client.workflows_get.return_value = wd
    mocker.patch(
        "nb_workflows.executors.docker.docker.from_env", return_value=docker_client
    )
    mocker.patch("nb_workflows.client.minimal_client", return_value=nb_client)
    s = SchedulerExecutor(redis, qname="test", is_async=False)
    j = s.enqueue_notebook_in_docker("test_prj", "test_key", nb_task_schedule)

    assert j.is_finished == True
