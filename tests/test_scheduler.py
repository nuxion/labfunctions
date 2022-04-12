import pickle

from pytest_mock import MockerFixture
from rq.job import Job

from nb_workflows import scheduler
from nb_workflows.executors.context import ExecID
from nb_workflows.scheduler import control_q, firm_or_new, machine_q

from .factories import ExecutionNBTaskFactory, WorkflowDataFactory


def test_scheduler_control_q():
    qname = control_q()
    assert qname == "ctrl.control"


def test_scheduler_machine_q():
    qname = machine_q(name="default")
    assert qname == "mch.default"


def test_scheduler_firm_or_new():
    signed = firm_or_new("test", "dispatcher")
    non_id = firm_or_new(None, "web")
    assert signed == f"{ExecID.firms.dispatcher}.test"
    assert non_id.startswith(f"{ExecID.firms.web}.")


def test_scheduler_instance(redis):

    s = scheduler.SchedulerExecutor(redis, qname="test", is_async=False)
    assert isinstance(s, scheduler.SchedulerExecutor)


def test_scheduler_dispatcher(mocker: MockerFixture, connection, redis):

    exec_ctx = ExecutionNBTaskFactory(projectid="test", wfid="test")

    mocker.patch("nb_workflows.executors.docker.docker_exec", return_value=True)
    mocker.patch(
        "nb_workflows.scheduler.workflows_mg.prepare_notebook_job",
        return_value=exec_ctx,
    )

    scheduler_mock = mocker.MagicMock()
    scheduler_mock.enqueue_notebook.return_value = None
    mocker.patch(
        "nb_workflows.scheduler.SchedulerExecutor", return_value=scheduler_mock
    )

    scheduler.scheduler_dispatcher("test", "test", redis_obj=redis)

    assert scheduler_mock.method_calls[0].args[0].execid == exec_ctx.execid


def test_scheduler_SEdispatcher(mocker: MockerFixture, redis):

    exec_ctx = ExecutionNBTaskFactory(projectid="test", wfid="test")

    mocker.patch("nb_workflows.executors.docker.docker_exec", return_value=True)
    mocker.patch(
        "nb_workflows.scheduler.workflows_mg.prepare_notebook_job",
        return_value=exec_ctx,
    )

    se = scheduler.SchedulerExecutor(redis, qname="test", is_async=False)

    job: Job = se.dispatcher("test", wfid="test")
    job_execid: Job = se.dispatcher("test", wfid="test", execid="testid")

    assert isinstance(job, Job)
    assert job_execid.id == f"{ExecID.firms.dispatcher}.testid"


def test_scheduler_SE_notebook(mocker: MockerFixture, redis):

    exec_ctx = ExecutionNBTaskFactory(projectid="test", wfid="test")

    nb_client = mocker.MagicMock()
    docker_client = mocker.MagicMock()

    wd = WorkflowDataFactory()
    docker_client.containers.run.return_value = "OK"
    nb_client.workflows_get.return_value = wd
    nb_client.projects_private_key.return_value = "private"
    mocker.patch(
        "nb_workflows.executors.docker.docker.from_env", return_value=docker_client
    )
    mocker.patch("nb_workflows.client.agent", return_value=nb_client)

    se = scheduler.SchedulerExecutor(redis, qname="test", is_async=False)
    job = se.enqueue_notebook(exec_ctx, qname="test")
    assert job.id == exec_ctx.execid
