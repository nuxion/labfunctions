from typing import List, Optional, Union

from pydantic import BaseModel, BaseSettings

from nb_workflows import defaults


class GoogleConf(BaseSettings):
    service_account: str
    pem_file: str
    project: str
    datacenter: str
    default_image: str = defaults.GCLOUD_IMG

    class Config:
        env_prefix = "NB_G"


class DigitalOceanConf(BaseSettings):
    acces_token: str
    api_version: str = "v2"

    class Config:
        env_prefix = "NB_DO"


class SSHKey(BaseModel):
    public: str
    private: Optional[str] = None
    user: str = "op"


class NodeInstance(BaseModel):
    name: str
    size: str
    image: str
    location: str  # zone
    ssh_public: Optional[str] = None
    ssh_user: str = "op"
    network: str = "default"
    tags: Optional[List[str]] = None


class MachineType(BaseModel):
    size: str
    image: str
    location: str  # zone
    vcpus: int = 1
    network: str = "default"


class MachineOrm(BaseModel):
    name: str
    provider: str
    machine_type: MachineType
    desc: Optional[str] = None


class ExecutionMachine(BaseModel):
    execid: str
    machine_name: str
    provider: str
    ssh_key: SSHKey
    node: NodeInstance
    qnames: str
    docker_version: str
    worker_homedir: str
    worker_env_file: str
    # worker_name: str
    worker_procs: int = 1


class ExecMachineResult(BaseModel):
    execid: str
    private_ips: List[str]
    public_ips: Optional[List[str]] = None
    node: NodeInstance
