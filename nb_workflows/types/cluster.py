from typing import List, Optional, Union

from pydantic import BaseModel, BaseSettings

from nb_workflows.conf import defaults


class GoogleConf(BaseSettings):
    service_account: str
    pem_file: str
    project: str
    datacenter: str
    default_image: str = defaults.GCLOUD_IMG

    class Config:
        env_prefix = "NB_G"


class NodeInstance(BaseModel):
    name: str
    size: str
    image: str
    location: str  # zone
    ssh_key_user: str = "op"
    ssh_publickey: Optional[str] = None
    network: Optional[str] = None
    tags: Optional[List[str]] = None


class MachineType(BaseModel):
    size: str
    image: str
    location: str  # zone
    network: Optional[str] = None


class MachineOrm(BaseModel):
    name: str
    provider: str
    machine_type: MachineType
    desc: Optional[str] = None
