import tempfile
import time
from typing import Any, Dict, List, Optional

from asyncssh.process import SSHCompletedProcess
from tenacity import retry, stop_after_attempt, wait_random

from labfunctions import defaults
from labfunctions.cluster import ssh
from labfunctions.cluster.utils import ssh_from_settings
from labfunctions.conf.jtemplates import render_to_file
from labfunctions.types import ServerSettings
from labfunctions.types.agent import AgentRequest
from labfunctions.utils import execute_cmd_no_block, get_version, run_sync


def _prepare_agent_cmd(
    ip_address: str,
    machine_id: str,
    cluster: str,
    qnames: str,
    workers_n=1,
):
    """
    It will run nb agent command.
    Name is not provided, so the agent will choose their name.
    """

    cmd = f"nb agent -i {ip_address} -C {cluster} -q {qnames} -w {workers_n} -m {machine_id}"
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

    nb_agent_cmd = _prepare_agent_cmd(
        ip_address, machine_id, cluster, qnames, workers_n
    )

    cmd = (
        f"docker run -d -v /var/run/docker.sock:/var/run/docker.sock "
        f"-e LF_SERVER=true  --env-file={env_file} "
        f"{docker_image}:{docker_version} "
        f"{nb_agent_cmd}"
    )
    return cmd


@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
def agent(req: AgentRequest, data_settings: Dict[str, Any]) -> SSHCompletedProcess:
    """
    Deploy an agent into a server, it has two steps:
    render and copy a .env.docker file into the remote server
    and pull and start the agent's docker instance
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = f"{tmpdir}/.env.docker"
        render_to_file(defaults.AGENT_ENV_TPL, env_file, data=data_settings)
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


def agent_local(req: AgentRequest, data_settings: Dict[str, Any], use_docker=False):

    addr = req.advertise_addr or req.machine_ip
    env_file = f"{req.agent_homedir}/.env.docker"
    render_to_file(defaults.AGENT_ENV_TPL, env_file, data=data_settings)

    if use_docker:
        cmd = _prepare_docker_cmd(
            addr,
            machine_id=req.machine_id,
            qnames=",".join(req.qnames),
            cluster=req.cluster,
            env_file=env_file,
            docker_image=req.docker_image,
            docker_version=req.docker_version,
            workers_n=req.worker_procs,
        )
    else:
        cmd = _prepare_agent_cmd(
            addr,
            machine_id=req.machine_id,
            cluster=req.cluster,
            qnames=",".join(req.qnames),
            workers_n=req.worker_procs,
        )

    result = execute_cmd_no_block(cmd, check=False)
    return {"pid": result.pid}


def agent_from_settings(
    ip,
    machine_id,
    cluster,
    settings: ServerSettings,
    qnames: List[str],
    worker_procs=1,
    docker_version=None,
) -> AgentRequest:
    key = ssh_from_settings(settings)
    version = docker_version or get_version()
    return AgentRequest(
        machine_ip=ip,
        machine_id=machine_id,
        private_key_path=key.private_path,
        cluster=cluster,
        qnames=qnames,
        agent_homedir=settings.AGENT_HOMEDIR,
        docker_version=version,
        worker_procs=worker_procs,
    )
