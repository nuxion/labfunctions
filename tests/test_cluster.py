from pytest_mock import MockerFixture

from labfunctions.cluster import deploy
from labfunctions.cluster.context import create_machine_ctx, machine_from_settings
from labfunctions.conf.server_settings import settings
from labfunctions.types.agent import AgentNode, AgentRequest
from labfunctions.types.machine import (
    ExecutionMachine,
    MachineGPU,
    MachineRequest,
    SSHKey,
)
from labfunctions.utils import get_version

from .factories import MachineOrmFactory


def test_cluster_create_machine_ctx():
    m1 = MachineOrmFactory(gpu=None)
    m1.machine_type.vcpus = 5

    ssh = SSHKey(public_path="tests/dummy_rsa.pub", user="pytest")
    ctx = create_machine_ctx(m1, ["default"], "test")

    gpu = MachineGPU(name="test", gpu_type="tesla", count=1)
    m2 = MachineOrmFactory(gpu=gpu)
    ctx_full = create_machine_ctx(
        m2, ["default"], "test", ssh_key=ssh, dynamic_workers=False
    )
    assert isinstance(ctx, ExecutionMachine)
    assert isinstance(ctx.machine, MachineRequest)
    assert ctx.worker_procs == 5
    assert ctx.ssh_key is None
    assert ctx.machine.ssh_user is None
    assert ctx.machine.labels["gpu"] == "no"
    assert isinstance(ctx_full.ssh_key, SSHKey)
    assert ctx_full.machine.ssh_user == "pytest"
    assert isinstance(ctx_full.machine.gpu, MachineGPU)
    assert ctx_full.machine.labels["gpu"] == "yes"
    assert ctx.machine.labels["tags"][0] == "nbworkflows"


def test_cluster_machine_from_settings():
    execm = machine_from_settings("gce-small-gpu", "default", ["default"], settings)
    ctx_net = machine_from_settings(
        "gce-small-gpu",
        "default",
        ["default"],
        settings,
        network="pytest",
        location="new-york",
    )
    assert isinstance(execm, ExecutionMachine)
    assert isinstance(execm.machine.gpu, MachineGPU)
    assert execm.machine.gpu.gpu_type == "nvidia-tesla-t4"
    assert ctx_net.machine.network == "pytest"
    assert ctx_net.machine.location == "new-york"


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
        "labfunctions.cluster.deploy.run_sync", side_effect=["test", "ok"]
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

    mocker.patch("labfunctions.cluster.deploy.render_to_file", return_value=None)
    spy = mocker.patch(
        "labfunctions.cluster.deploy.execute_cmd_no_block", return_value=cmd_rsp
    )
    result_with_docker = deploy.agent_local(req, settings.dict(), use_docker=True)

    result = deploy.agent_local(req, settings.dict(), use_docker=False)
    assert result_with_docker["pid"] == "ok"
    assert "docker" in spy.call_args_list[0][0][0]
    assert "docker" not in spy.call_args_list[1][0][0]
