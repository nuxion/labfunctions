import tempfile
from typing import List, Optional

from labfunctions import defaults
from labfunctions.cluster import ssh
from labfunctions.conf.jtemplates import render_to_file
from labfunctions.types import ServerSettings
from labfunctions.types.agent import AgentRequest
from labfunctions.utils import run_sync


def _prepare_agent_cmd(
    ip_address: str,
    qnames: str,
    env_file=".env.dev.docker",
    workers=1,
):

    cmd = f"nb agent -w {workers} -i {ip_address} -q {qnames}"
    return cmd


def _prepare_docker_cmd(
    ip_address: str,
    qnames: str,
    docker_image: str,
    env_file=".env.dev.docker",
    workers=1,
    docker_version="latest",
):

    nb_agent_cmd = _prepare_agent_cmd(ip_address, qnames, env_file, workers)

    cmd = (
        f"docker run -d -v /var/run/docker.sock:/var/run/docker.sock "
        f"-e LF_SERVER=true  --env-file={env_file} "
        f"{docker_image}:{docker_version} "
        f"{nb_agent_cmd}"
    )
    return cmd


def agent(settings: ServerSettings, req: AgentRequest):
    """
    Deploy an agent into a server, it has two steps:
    render and copy a .env.docker file into the remote server
    and pull and start the agent's docker instance
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = f"{tmpdir}/.env.docker"
        render_to_file(defaults.AGENT_ENV_TPL, env_file)
        run_sync(
            ssh.scp_from_local,
            remote_addr=req.node_ip,
            remote_dir=req.agent_homedir,
            local_file=env_file,
            keys=[req.private_key_path],
        )

    agent_env_file = f"{req.agent_homedir}/.env.docker"
    addr = req.advertise_addr or req.node_ip
    cmd = _prepare_docker_cmd(
        addr,
        qnames=",".join(req.qnames),
        docker_image=req.docker_image,
        env_file=agent_env_file,
        workers=req.worker_procs,
        docker_version=req.docker_version,
    )

    result = run_sync(ssh.run_cmd, req.node_ip, cmd, keys=[req.private_key_path])
    return result
