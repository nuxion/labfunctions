from nb_workflows.cluster.context import create_machine_ctx, machine_from_settings
from nb_workflows.cluster.utils import prepare_agent_cmd, prepare_docker_cmd
from nb_workflows.conf.server_settings import settings
from nb_workflows.types.cluster import ExecMachineResult, ExecutionMachine, MachineOrm

# def test_machine_create_machine_ctx():
#     mo = MachineOrmFactory()
#     ssh = SSHKey(public="tests/dummy_rsa.pub", user="op")
#     ctx = context.create_machine_ctx(mo, ssh, worker_env_file="test.txt")
#     assert isinstance(ctx, ExecutionMachine)
#     assert ctx.qnames == mo.name
#     assert isinstance(ctx.node, NodeInstance)


def test_cluster_machine_from_settings():
    execm = machine_from_settings("local", ["default"], settings)
    assert isinstance(execm, ExecutionMachine)


def test_cluster_prepare_agent_cmd():
    cmd = prepare_agent_cmd("127.0.0.1", qnames="default", workers=3)
    assert cmd == "nb agent -w 3 -i 127.0.0.1 -q default"


def test_cluster_prepare_docker():
    cmd = prepare_docker_cmd(
        "127.0.0.1", qnames="default", docker_image="nuxion/nb", workers=3
    )

    assert "nuxion/nb:latest" in cmd
