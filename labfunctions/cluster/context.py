from typing import Any, Dict, List, Optional, Union

from labfunctions import defaults, errors
from labfunctions.hashes import generate_random
from labfunctions.types import ServerSettings
from labfunctions.types.machine import (
    BlockStorage,
    ExecutionMachine,
    MachineGPU,
    MachineOrm,
    MachineRequest,
    SSHKey,
)
from labfunctions.utils import get_version, open_publickey, open_yaml

from .inventory import Inventory
from .utils import get_local_machine, get_local_volume, ssh_from_settings


def create_machine_ctx(
    machine: MachineOrm,
    qnames: List[str],
    cluster: str,
    agent_homedir=defaults.AGENT_HOMEDIR,
    volumes: List[BlockStorage] = [],
    ssh_key: Optional[SSHKey] = None,
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

    _id = generate_random(size=6, alphabet=defaults.NANO_MACHINE_ALPHABET)
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

    gpu = "no"
    if machine.gpu:
        gpu = "yes"

    labels = {"cluster": cluster, "gpu": gpu, "tags": [defaults.CLOUD_TAG]}

    req = MachineRequest(
        name=name,
        ssh_public_cert=public_key,
        ssh_user=ssh_user,
        gpu=machine.gpu,
        image=type_.image,
        volumes=volumes,
        size=type_.size,
        location=machine.location,
        network=type_.network,
        labels=labels,
    )
    ctx = ExecutionMachine(
        execid=execid,
        machine_name=name,
        machine=req,
        provider=machine.provider,
        cluster=cluster,
        qnames=qnames,
        agent_homedir=agent_homedir,
        worker_procs=worker_procs,
        ssh_key=ssh_key,
        docker_uid=docker_uid,
        docker_gid=docker_gid,
        docker_image=docker_image,
        docker_version=version,
    )
    return ctx


def machine_from_settings(
    machine_name: str,
    cluster: str,
    qnames: List[str],
    settings: ServerSettings,
    network: Optional[str] = None,
    location: Optional[str] = None,
    docker_version=None,
    inventory: Optional[Inventory] = None,
) -> ExecutionMachine:
    """It will create a context from settings and the inventory file
    if network or location are set (mainly from the clusterspec) then
    it will will overwrite the definition from inventory.
    """

    inventory = inventory or Inventory()

    m: MachineOrm = inventory.machines[machine_name]
    if network:
        m.machine_type.network = network
    if location:
        m.location = location
    volumes = [inventory.volumes[vol] for vol in m.volumes]

    ssh = ssh_from_settings(settings)
    # agent_env_file = settings.AGENT_ENV_FILE
    ctx = create_machine_ctx(
        m,
        qnames,
        cluster,
        volumes=volumes,
        agent_homedir=settings.AGENT_HOMEDIR,
        ssh_key=ssh,
        docker_version=docker_version,
        docker_uid=settings.DOCKER_UID,
        docker_gid=settings.DOCKER_GID,
    )
    return ctx
