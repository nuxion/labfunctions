from typing import Dict, Union

from labfunctions.types import ServerSettings
from labfunctions.types.cluster import ClusterSpec
from labfunctions.types.machine import BlockStorage, MachineOrm, SSHKey
from labfunctions.utils import open_yaml


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
