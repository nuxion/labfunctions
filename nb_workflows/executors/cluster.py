from typing import List

import asyncssh
from asyncssh.process import SSHCompletedProcess

from nb_workflows.conf import defaults
from nb_workflows.hashes import generate_random
from nb_workflows.types.cluster import ExecMachineResult, ExecutionMachine

WORKER_INIT = "docker run --rm "


def prepare_worker_cmd(
    ip_address: str,
    qnames: str,
    env_file=".env.dev.docker",
    workers=1,
    worker_name=None,
    version="0.7.0",
):

    cmd = (
        f"docker run -d -v /var/run/docker.sock:/var/run/docker.sock "
        f"-e NB_SERVER=true  --env-file={env_file} "
        f"{defaults.WORKER_DOCKER_IMG}:{version} "
        f"nb rqworker -w {workers} -i {ip_address} -q {qnames} "
    )
    return cmd


def create_gcloud(ctx: ExecutionMachine):
    from nb_workflows.cluster.gcloud import create_driver, create_instance

    driver = create_driver()
    node = create_instance(driver, ctx.node)
    return node


def destroy_gcloud(name: str):
    from nb_workflows.cluster.gcloud import create_driver, destroy_instance

    driver = create_driver()
    destroy_instance(driver, name)


async def run_ssh(
    addr: str, cmd: str, keys: List[str], username="op", known_hosts=None, check=False
) -> SSHCompletedProcess:
    """
    A opinated wrapper around asyncssh
    :param addr: ip address to connect
    :param cmd: a simple string with the command to run
    :param keys: a List of keys names to be used without extension
    :param username: user to use for ssh connection
    :param known_hosts: validate server host, if None this check will ignored
    :param check: if true an a remote error happend it will raise an exceptions
    """

    async with asyncssh.connect(
        addr, username=username, client_keys=keys, known_hosts=known_hosts
    ) as conn:
        result = await conn.run(cmd, check=check)
    return result


async def scp_from_local(
    remote_addr: str,
    remote_dir: str,
    local_file: str,
    keys: List[str],
    username="op",
    known_hosts=None,
):
    """
    Copy a local file to remote server
    :param remote_addr: ip address to connect
    :param remote_dir: dir where files should be copied
    :param local_file: local file to be copied
    :param keys: a List of keys names to be used without extension
    :param username: user to use for ssh connection
    :param known_hosts: validate server host, if None this check will ignored
    """

    async with asyncssh.connect(
        remote_addr, username=username, client_keys=keys, known_hosts=known_hosts
    ) as conn:
        await asyncssh.scp(local_file, (conn, remote_dir))


async def deploy_in_node(addr, ctx: ExecutionMachine) -> SSHCompletedProcess:
    key = ctx.ssh_key.private
    await scp_from_local(
        remote_addr=addr,
        remote_dir=ctx.worker_homedir,
        local_file=ctx.worker_env_file,
        keys=[key],
    )

    cmd = prepare_worker_cmd(
        addr, qnames=ctx.qnames, workers=ctx.worker_procs, version=ctx.docker_version
    )

    result = await run_ssh(addr, cmd, keys=[key])

    return result


def create_machine(ctx: ExecutionMachine) -> ExecMachineResult:
    from nb_workflows.qworker import settings

    if ctx.provider == "gcloud":
        node = create_gcloud(ctx)

    res = ExecMachineResult(
        execid=ctx.execid,
        private_ips=node.private_ips,
        public_ips=node.public_ips,
        node=ctx.node,
    )
    return res


def destroy_machine(name: str):
    pass
