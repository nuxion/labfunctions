from typing import Dict, Union

from nb_workflows.types import ServerSettings
from nb_workflows.types.cluster import BlockStorage, MachineOrm, SSHKey
from nb_workflows.utils import open_yaml


def prepare_agent_cmd(
    ip_address: str,
    qnames: str,
    env_file=".env.dev.docker",
    workers=1,
):

    cmd = f"nb agent -w {workers} -i {ip_address} -q {qnames}"
    return cmd


def prepare_docker_cmd(
    ip_address: str,
    qnames: str,
    docker_image: str,
    env_file=".env.dev.docker",
    workers=1,
    docker_version="latest",
):

    nb_agent_cmd = prepare_agent_cmd(ip_address, qnames, env_file, workers)

    cmd = (
        f"docker run -d -v /var/run/docker.sock:/var/run/docker.sock "
        f"-e NB_SERVER=true  --env-file={env_file} "
        f"{docker_image}:{docker_version} "
        f"{nb_agent_cmd}"
    )
    return cmd


def get_local_machine(name, data) -> MachineOrm:
    return MachineOrm(**data["machines"][name])


def get_local_volume(name, data) -> BlockStorage:
    return BlockStorage(**data["volumes"][name])


def ssh_from_settings(settings: ServerSettings) -> Union[SSHKey, None]:

    if settings.CLUSTER_SSH_PUBLIC_KEY:
        ssh = SSHKey(
            user=settings.CLUSTER_SSH_KEY_USER,
            public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        )

        ssh.private_path = ssh.public_path.split(".pub")[0]
        return ssh
    return None
