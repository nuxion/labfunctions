from typing import Dict, Union

from nb_workflows.types import ServerSettings
from nb_workflows.types.cluster import ClusterSpec
from nb_workflows.types.machine import BlockStorage, MachineOrm, SSHKey
from nb_workflows.utils import open_yaml


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
