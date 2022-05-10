from typing import Any, Dict, List, NewType, Optional, Set, Tuple, Union

from pydantic import BaseModel, BaseSettings

from labfunctions import defaults


class DataFolder(BaseModel):
    projectid: str
    name: str
    provider: str
    location: str
    volume_name: str


class ScaleItems(BaseModel):
    """It scale by items enqueue in Redis queue"""

    qname: str
    items_gt: int
    items_lt: int = -1
    increase_by: int = 1
    decrease_by: int = 1
    name: str = "items"


class ScaleIdle(BaseModel):
    """idle_time in minutes"""

    idle_time_gt: int
    idle_time_lt: Optional[int] = None
    name: str = "idle"


class ScaleTimeframe(BaseModel):
    pass


class ClusterState(BaseModel):
    agents_n: int
    agents: Set[str]
    queue_items: Dict[str, int]
    idle_by_agent: Dict[str, int]
    # machines:


class ClusterPolicy(BaseModel):
    min_nodes: int
    max_nodes: int
    strategies: List[Any] = []
    default_nodes: Optional[int] = None


class ClusterDiff(BaseModel):
    to_delete: List[str]
    to_create: int


class ClusterSpec(BaseModel):
    name: str
    provider: str
    machine: str
    location: str
    qnames: List[str]
    policy: ClusterPolicy
    network: str = "default"


class ClusterFile(BaseModel):
    clusters: Dict[str, ClusterSpec]
    inventory: Optional[str] = None
    default_cluster: Optional[str] = None
