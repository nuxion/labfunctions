from typing import Optional

import redis

from labfunctions.control_plane.register import AgentRegister
from labfunctions.errors.cluster import ClusterSpecNotFound
from labfunctions.types.cluster import ClusterSpec

from .cluster_file import load_cluster_file
from .control import ClusterControl
from .inventory import Inventory


def get_spec_from_file(from_file: str, cluster=None) -> ClusterSpec:
    cluster_file = load_cluster_file(from_file)
    try:
        cluster = cluster or cluster_file.default_cluster
        spec = cluster_file.clusters[cluster]
    except KeyError:
        raise ClusterSpecNotFound(cluster, from_file)
    return spec


def create_cluster_control(
    from_file: str, register_url: str, cluster: Optional[str] = None
) -> ClusterControl:
    cluster_file = load_cluster_file(from_file)
    spec = get_spec_from_file(from_file, cluster)

    inventory = Inventory(cluster_file.inventory)
    rdb = redis.from_url(register_url, decode_responses=True)
    registry = AgentRegister(rdb, cluster)
    cc = ClusterControl(registry, spec=spec, inventory=inventory)
    return cc
