from typing import Any, Dict, List, NewType, Optional, Tuple, Union

from pydantic import BaseModel, BaseSettings

from nb_workflows import defaults

ExtraField = NewType("ExtraField", Dict[str, Any])


class SSHKey(BaseModel):
    """
    It represents a SSHKey configuration,
    it will have the paths to public and private key
    and user associated to that key
    """

    public_path: str
    private_path: Optional[str] = None
    user: str = "op"


class MachineType(BaseModel):
    """A generic Machine type to be used in MachineModel"""

    size: str
    image: str
    vcpus: int = 1
    network: str = "default"
    extra: Optional[ExtraField] = None


class MachineGPU(BaseModel):
    """A generic representation of GPU resource"""

    name: str
    gpu_type: str
    number: int = 1
    extra: ExtraField = None


class BlockStorage(BaseModel):
    """
    A generic representation of a disk, potentially the mount_point could
    be used to identify if this will be a boot disk (needed in GCE)
    """

    name: str
    size: Union[int, str]
    location: str
    mount: str = "/mnt/disk0"
    snapshot: Optional[str] = None
    permissions: Optional[List[str]] = None
    description: Optional[str] = None
    kind: Optional[str] = None
    extra: Optional[ExtraField] = None


class MachineOrm(BaseModel):
    """Entity representing the MachineModel"""

    name: str
    provider: str
    location: str  # zone
    machine_type: MachineType
    gpu: Optional[MachineGPU] = None
    volumes: List[str] = []
    desc: Optional[str] = None

    class Config:
        orm_mode = True


class NodeRequest(BaseModel):
    """
    Node Request definition, this will be used as a request to
    create a machine

    :param name: the machine will be created with this name, usually
    is build as `machine-type`-`random_id`
    :param size: node type in vendor cloud
    :param image: image to be used like debian or custom
    :param location: a general term, cloud providers could use zone, region or both
    :param disks: Disks to be attached to the machine creation
    :param gpu: Optional GPU resource
    :param ssh_public_cert: certificate to be added to authorized_keys
    in the remote host
    :param ssh_user: to which user allow access
    :param network: virtual network to configurate
    :param tags: tags to be used

    """

    name: str
    size: str
    image: str
    location: str  # zone
    volumes: List[BlockStorage] = []
    gpu: Optional[MachineGPU] = None
    ssh_public_cert: Optional[str] = None
    ssh_user: str = "op"
    network: str = "default"
    tags: Optional[List[str]] = None


class NodeInstance(BaseModel):
    node_id: str
    node_name: str
    location: str
    private_ips: List[str]
    public_ips: Optional[List[str]] = None
    main_addr: Optional[str] = None
    extra: Optional[ExtraField] = None


class BlockInstance(BaseModel):
    id: str
    name: str
    size: Union[int, str]
    location: str
    mount: Optional[str] = None
    snapshot: Optional[str] = None
    permissions: Optional[List[str]] = None
    description: Optional[str] = None
    kind: Optional[str] = None
    extra: Optional[ExtraField] = None


class ExecutionMachine(BaseModel):
    execid: str
    machine_name: str
    provider: str
    node: NodeRequest
    qnames: List[str]
    agent_homedir: str
    agent_env_file: str
    worker_procs: int = 1
    ssh_key: Optional[SSHKey] = None
    docker_uid: str = defaults.DOCKER_UID
    docker_gid: str = defaults.DOCKER_GID
    docker_image: str = defaults.AGENT_DOCKER_IMG
    docker_version: str = "latest"


class ExecMachineResult(BaseModel):
    execid: str
    private_ips: List[str]
    public_ips: Optional[List[str]] = None
    node: NodeInstance


class AgentNode(BaseModel):
    """
    A self register entity for each machine created
    """

    ip_address: str
    name: str
    pid: str
    qnames: List[str]
    workers: List[str]
    birthday: int


class AgentConfig(BaseModel):
    redis_dsn: str
    qnames: List[str]
    ip_address: str
    heartbeat_ttl: int
    heartbeat_check_every: int
    name: Optional[str] = None
    workers_n = 1
