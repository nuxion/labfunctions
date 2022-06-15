import tempfile
import time
from typing import Any, Dict, List, Optional

from asyncssh.process import SSHCompletedProcess
from tenacity import retry, stop_after_attempt, wait_random

from labfunctions import defaults
from labfunctions.cluster import ssh
from labfunctions.cluster.types import AgentRequest
from labfunctions.conf.jtemplates import render_to_file
from labfunctions.types import ServerSettings
from labfunctions.utils import execute_cmd_no_block, get_version, run_sync


def _prepare_agent_cmd(
    ip_address: str,
    machine_id: str,
    cluster: str,
    qnames: str,
    workers_n=1,
) -> str:
    """
    It will run nb agent command.
    Name is not provided, so the agent will choose their name.
    """

    cmd = (
        f"lab agent run -i {ip_address} -C {cluster} "
        f"-q {qnames} -w {workers_n} -m {machine_id}"
    )
    return cmd


def _prepare_docker_cmd(
    ip_address: str,
    machine_id: str,
    qnames: str,
    cluster: str,
    env_file: str,
    docker_image: str,
    docker_version="latest",
    workers_n=1,
):

    lab_agent_cmd = _prepare_agent_cmd(
        ip_address, machine_id, cluster, qnames, workers_n
    )

    cmd = (
        f"docker run -d -v /var/run/docker.sock:/var/run/docker.sock "
        f"-e LF_SERVER=true  --env-file={env_file} "
        f"{docker_image}:{docker_version} "
        f"{lab_agent_cmd}"
    )
    return cmd


@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
def agent(req: AgentRequest) -> SSHCompletedProcess:
    """
    Deploy an agent into a server, it has two steps:
    render and copy a .env.docker file into the remote server
    and pull and start the agent's docker instance
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = f"{tmpdir}/.env.docker"
        render_to_file(defaults.AGENT_ENV_TPL, env_file, data=req.dict())
        run_sync(
            ssh.scp_from_local,
            remote_addr=req.machine_ip,
            remote_dir=req.agent_homedir,
            local_file=env_file,
            keys=[req.private_key_path],
        )

    agent_env_file = f"{req.agent_homedir}/.env.docker"
    addr = req.advertise_addr or req.machine_ip
    cmd = _prepare_docker_cmd(
        addr,
        machine_id=req.machine_id,
        qnames=",".join(req.qnames),
        cluster=req.cluster,
        env_file=agent_env_file,
        docker_image=req.docker_image,
        docker_version=req.docker_version,
        workers_n=req.worker_procs,
    )
    result = run_sync(ssh.run_cmd, req.machine_ip, cmd, keys=[req.private_key_path])
    return result


async def agent_async(req: AgentRequest) -> SSHCompletedProcess:
    """
    Deploy an agent into a server, it has two steps:
    render and copy a .env.docker file into the remote server
    and pull and start the agent's docker instance
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = f"{tmpdir}/.env.docker"
        render_to_file(defaults.AGENT_ENV_TPL, env_file, data=req.dict())
        await ssh.scp_from_local(
            remote_addr=req.machine_ip,
            remote_dir=req.agent_homedir,
            local_file=env_file,
            keys=[req.private_key_path],
        )

    agent_env_file = f"{req.agent_homedir}/.env.docker"
    addr = req.advertise_addr or req.machine_ip
    cmd = _prepare_docker_cmd(
        addr,
        machine_id=req.machine_id,
        qnames=",".join(req.qnames),
        cluster=req.cluster,
        env_file=agent_env_file,
        docker_image=req.docker_image,
        docker_version=req.docker_version,
        workers_n=req.worker_procs,
    )
    result = await ssh.run_cmd(req.machine_ip, cmd, keys=[req.private_key_path])
    return result
