from pytest_mock import MockerFixture

from nb_workflows.cluster import deploy
from nb_workflows.cluster.context import create_machine_ctx, machine_from_settings
from nb_workflows.conf.server_settings import settings
from nb_workflows.types.agent import AgentNode, AgentRequest
from nb_workflows.types.machine import ExecutionMachine
from nb_workflows.utils import get_version

# def test_machine_create_machine_ctx():
#     mo = MachineOrmFactory()
#     ssh = SSHKey(public="tests/dummy_rsa.pub", user="op")
#     ctx = context.create_machine_ctx(mo, ssh, worker_env_file="test.txt")
#     assert isinstance(ctx, ExecutionMachine)
#     assert ctx.qnames == mo.name
#     assert isinstance(ctx.node, NodeInstance)


def test_cluster_deploy_machine_from_settings():
    execm = machine_from_settings("local", "local", ["default"], settings)
    assert isinstance(execm, ExecutionMachine)


def test_cluster_deploy_prepare_agent_cmd():
    cmd = deploy._prepare_agent_cmd(
        "127.0.0.1", "test-id", "test-cluster", qnames="default", workers_n=3
    )
    assert cmd == "nb agent -i 127.0.0.1 -C test-cluster -q default -w 3 -m test-id"


def test_cluster_deploy_prepare_docker():
    cmd = deploy._prepare_docker_cmd(
        "127.0.0.1",
        "test-id",
        qnames="default",
        cluster="test-cluster",
        env_file=".env.docler",
        docker_image="nuxion/nb",
        workers_n=3,
    )

    assert "nuxion/nb:latest" in cmd


def test_cluster_deploy_agent_from_settings():
    agt = deploy.agent_from_settings(
        "127.0.0.1",
        machine_id="test-id",
        cluster="test",
        settings=settings,
        qnames=["default"],
        docker_version="1",
    )

    agt2 = deploy.agent_from_settings(
        "127.0.0.1",
        machine_id="test-id",
        cluster="test",
        settings=settings,
        qnames=["default"],
    )

    version = get_version()

    assert agt.docker_version == "1"
    assert isinstance(agt, AgentRequest)
    assert agt2.docker_version == version


def test_cluster_deploy_agent(mocker: MockerFixture):
    req = deploy.agent_from_settings(
        "127.0.0.1",
        machine_id="test-id",
        cluster="test",
        settings=settings,
        qnames=["default"],
    )

    run_sync = mocker.patch(
        "nb_workflows.cluster.deploy.run_sync", side_effect=["test", "ok"]
    )
    result = deploy.agent(req, settings.dict())
    assert result == "ok"
    assert f"{req.agent_homedir}/.env.docker" in run_sync.call_args[0][2]


def test_cluster_deploy_agent_local(mocker: MockerFixture):
    req = deploy.agent_from_settings(
        "127.0.0.1",
        machine_id="test-id",
        cluster="test",
        settings=settings,
        qnames=["default"],
    )

    cmd_rsp = mocker.MagicMock()
    cmd_rsp.pid = "ok"

    mocker.patch("nb_workflows.cluster.deploy.render_to_file", return_value=None)
    spy = mocker.patch(
        "nb_workflows.cluster.deploy.execute_cmd_no_block", return_value=cmd_rsp
    )
    result_with_docker = deploy.agent_local(req, settings.dict(), use_docker=True)

    result = deploy.agent_local(req, settings.dict(), use_docker=False)
    assert result_with_docker["pid"] == "ok"
    assert "docker" in spy.call_args_list[0][0][0]
    assert "docker" not in spy.call_args_list[1][0][0]
