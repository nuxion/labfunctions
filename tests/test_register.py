from datetime import datetime

from pydantic import BaseModel
from pytest_mock import MockerFixture
from rq import command

from nb_workflows.control_plane import register, worker
from nb_workflows.types.cluster import AgentNode

now = int(datetime.utcnow().timestamp())

node_ag = AgentNode(
    ip_address="1.1", name="test", qnames=["test"], workers=["test.0"], birthday=now
)


class WorkerMocker(BaseModel):
    name: str


def test_register_register(redis):

    ag = register.AgentRegister(redis)
    ag.register(node_ag)
    data = redis.get("nb.ag.test")
    node = ag.get("test")

    nodes = ag.list_agents()
    ag.remove("test")
    removed = ag.get("test")

    assert data
    assert removed is None
    assert isinstance(node, AgentNode)
    assert len(nodes) == 1
    assert nodes[0] == "test"


def test_register_list_by_queue(mocker: MockerFixture, redis):
    workers = [WorkerMocker(name="test")]
    workers_m = mocker.MagicMock()
    workers_m.all.return_value = workers
    mocker.patch("nb_workflows.control_plane.register.Worker", workers_m)
    ag = register.AgentRegister(redis)

    data = ag.list_agents_by_queue("test")
    assert len(data) == 1


def test_register_list_agents(mocker: MockerFixture, redis):
    # workers = [WorkerMocker(name="test")]
    # mocker.patch(redis, "sinter", return_value=["test"])
    ag = register.AgentRegister(redis)
    redis.sinter = lambda x: ["test"]
    data = ag.list_agents()
    redis.sinter = lambda x: [b"test"]
    bdata = ag.list_agents()

    assert len(data) == 1
    assert len(bdata) == 1
    assert isinstance(bdata[0], str)


def test_register_kill_workers(mocker: MockerFixture, redis):
    spy = mocker.spy(register, "send_shutdown_command")

    workers = [WorkerMocker(name="test")]
    mocker.patch("nb_workflows.control_plane.register.Worker.all", return_value=workers)

    ag = register.AgentRegister(redis)
    ag.register(node_ag)

    ag.kill_workers_from_agent("test")
    assert spy.call_args[0][1] == node_ag.workers[0]


def test_register_kill_workers_q(mocker: MockerFixture, redis):
    spy = mocker.spy(register, "send_shutdown_command")

    workers = [WorkerMocker(name="test")]
    mocker.patch("nb_workflows.control_plane.register.Worker.all", return_value=workers)

    ag = register.AgentRegister(redis)
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
