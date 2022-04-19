from datetime import datetime

from pydantic import BaseModel
from pytest_mock import MockerFixture
from rq import command

from nb_workflows.control_plane import register, worker
from nb_workflows.types.agent import AgentNode

from .factories import AgentNodeFactory

now = int(datetime.utcnow().timestamp())


class WorkerMocker(BaseModel):
    name: str


def test_register_register(redis):

    node_ag = AgentNodeFactory()
    ag = register.AgentRegister(redis, "test")
    ag.register(node_ag)
    key = f"{ag.AGENT_PREFIX}.{node_ag.name}"
    data = redis.get(key)
    node = ag.get(node_ag.name)

    nodes = ag.list_agents()
    ag.remove(node_ag.name)
    removed = ag.get(node_ag.name)

    assert data
    assert removed is None
    assert isinstance(node, AgentNode)
    assert node_ag.name in nodes


def test_register_list_by_queue(mocker: MockerFixture, redis):
    workers = [WorkerMocker(name="test")]
    workers_m = mocker.MagicMock()
    workers_m.all.return_value = workers
    mocker.patch("nb_workflows.control_plane.register.NBWorker", workers_m)
    ag = register.AgentRegister(redis, "test")

    data = ag.list_agents_by_queue("test")
    assert len(data) == 1


def test_register_list_agents(mocker: MockerFixture, redis):
    # workers = [WorkerMocker(name="test")]
    # mocker.patch(redis, "sinter", return_value=["test"])
    ag = register.AgentRegister(redis, "test")
    redis.sinter = lambda x: ["test"]
    data = ag.list_agents()
    redis.sinter = lambda x: [b"test"]
    bdata = ag.list_agents()

    assert len(data) == 1
    assert len(bdata) == 1
    assert isinstance(bdata[0], str)


def test_register_kill_workers_ag(mocker: MockerFixture, redis):
    spy = mocker.patch("nb_workflows.control_plane.register.send_shutdown_command")

    node_ag = AgentNodeFactory()
    mocker.patch(
        "nb_workflows.control_plane.register.AgentRegister.get", return_value=node_ag
    )

    ag = register.AgentRegister(redis, "test")
    ag.register(node_ag)

    ag.kill_workers_from_agent("test")
    assert spy.call_count == len(node_ag.workers)


def test_register_kill_workers_q(mocker: MockerFixture, redis):
    spy = mocker.spy(register, "send_shutdown_command")

    workers = [WorkerMocker(name="test")]
    mocker.patch(
        "nb_workflows.control_plane.register.NBWorker.all", return_value=workers
    )

    node_ag = AgentNodeFactory()
    ag = register.AgentRegister(redis, "test")
    ag.register(node_ag)
    ag.kill_workers_from_queue("test")
    assert spy.call_args[0][1] == workers[0].name


def test_worker_ip(redis):
    w = worker.NBWorker("test", name="test", connection=redis)
    w.set_ip_address("127.0.0.1")
    w.birth_date = datetime.utcnow()
    t = w.inactive_time()

    assert w.ip_address == "127.0.0.1"
    assert isinstance(t, int)


def test_worker_start(mocker: MockerFixture, redis):

    # conn = mocker.MagicMock()
    mocker.patch("nb_workflows.control_plane.worker.redis.from_url", return_value=redis)
    m = mocker.patch(
        "nb_workflows.control_plane.worker.NBWorker.work", return_value=None
    )

    worker.start_worker("redis://localhost:6379", ["test"], "127.0.0.1", name="test")

    assert m.called
