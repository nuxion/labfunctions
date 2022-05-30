from typing import List, Optional

from pydantic import BaseModel

from labfunctions import defaults


class AgentNode(BaseModel):
    """
    A self register entity for each machine created
    """

    ip_address: str
    name: str
    pid: str
    qnames: List[str]
    cluster: str
    workers: List[str]
    birthday: int
    machine_id: Optional[str] = None


class AgentConfig(BaseModel):
    redis_dsn: str
    cluster: str
    qnames: List[str]
    ip_address: str
    machine_id: str
    heartbeat_ttl: int
    heartbeat_check_every: int
    agent_name: Optional[str] = None
    workers_n = 1
    max_jobs: int = 10


class AgentRequest(BaseModel):
    machine_ip: str
    machine_id: str
    private_key_path: str
    cluster: str
    qnames: List[str] = ["default"]
    agent_homedir: str = defaults.AGENT_HOMEDIR
    agent_name: Optional[str] = None
    advertise_addr: Optional[str] = None
    docker_image: str = defaults.AGENT_DOCKER_IMG
    docker_version: str = "latest"
    worker_procs: int = 1
