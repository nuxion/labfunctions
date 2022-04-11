from nb_workflows.conf.types import ServerSettings
from nb_workflows.types.cluster import MachineOrm, SSHKey
from nb_workflows.utils import open_yaml


def get_local_machine(name, fp="scripts/machines.yaml") -> MachineOrm:
    data = open_yaml(fp)
    return MachineOrm(**data["machines"][name])


def ssh_from_settings(settings: ServerSettings) -> SSHKey:
    return SSHKey(
        user=settings.CLUSTER_SSH_KEY_USER, public=settings.CLUSTER_SSH_PUBLIC_KEY
    )
