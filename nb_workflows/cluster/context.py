from typing import List, Optional

from nb_workflows import defaults, errors
from nb_workflows.hashes import generate_random
from nb_workflows.types import ServerSettings
from nb_workflows.types.cluster import (
    BlockStorage,
    ExecutionMachine,
    MachineGPU,
    MachineOrm,
    NodeRequest,
    SSHKey,
)
from nb_workflows.utils import get_version, open_publickey, open_yaml

from .utils import get_local_machine, get_local_volume, ssh_from_settings


def create_machine_ctx(
    machine: MachineOrm,
    qnames: List[str],
    agent_env_file: str,
    agent_homedir=defaults.AGENT_HOMEDIR,
    volumes: List[BlockStorage] = [],
    ssh_key: Optional[SSHKey] = None,
    tags: List[str] = [],
    dynamic_workers=True,
    docker_uid=defaults.DOCKER_UID,
    docker_gid=defaults.DOCKER_GID,
    docker_image=defaults.AGENT_DOCKER_IMG,
    docker_version=None,
) -> ExecutionMachine:
    """
    Its build a machine execution context

    :param machine: A MachineOrm instance
    :param ssh_key: keys for the worker
    :param tags: A list of tags to put to the VM created in the cloud provider
    :param dynamic_workers: if true it will use vcpus in machine_type to allocate workers,
    if false, then only one worker will be allocated.
    """

    execid = f"mch.{generate_random(8)}"
    version = docker_version or get_version()

    _id = generate_random(size=10, alphabet=defaults.NANO_MACHINE_ALPHABET)
    name = f"{machine.name}-{_id}"
    type_ = machine.machine_type
    worker_procs = 1
    if dynamic_workers:
        worker_procs = machine.machine_type.vcpus

    public_key = None
    ssh_user = None
    if ssh_key:
        public_key = open_publickey(ssh_key.public_path)
        ssh_user = ssh_key.user

    node = NodeRequest(
        name=name,
        ssh_public_cert=public_key,
        ssh_user=ssh_user,
        image=type_.image,
        volumes=volumes,
        size=type_.size,
        location=machine.location,
        network=type_.network,
        tags=tags,
    )
    ctx = ExecutionMachine(
        execid=execid,
        machine_name=name,
        provider=machine.provider,
        node=node,
        qnames=qnames,
        agent_env_file=agent_env_file,
        agent_homedir=agent_homedir,
        ssh_key=ssh_key,
        worker_procs=worker_procs,
        docker_image=docker_image,
        docker_version=version,
    )
    return ctx


def machine_from_settings(
    machine_name: str,
    qnames: List[str],
    settings: ServerSettings,
    tags: List[str] = [],
    docker_version=None,
    fp="scripts/machines.yaml",
) -> ExecutionMachine:

    data = open_yaml(fp)
    m = get_local_machine(machine_name, data)
    volumes = [get_local_volume(vol, data) for vol in m.volumes]

    ssh = ssh_from_settings(settings)
    agent_env_file = settings.AGENT_ENV_FILE
    ctx = create_machine_ctx(
        m,
        qnames,
        agent_env_file,
        volumes=volumes,
        agent_homedir=settings.AGENT_HOMEDIR,
        ssh_key=ssh,
        docker_version=docker_version,
        docker_uid=settings.DOCKER_UID,
        docker_gid=settings.DOCKER_GID,
        tags=tags,
    )
    return ctx
