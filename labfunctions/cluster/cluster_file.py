from typing import Any, Dict, List

from labfunctions.types.cluster import ClusterFile, ClusterSpec, ScaleIdle, ScaleItems
from labfunctions.utils import open_yaml

STRATEGIES = {"items": ScaleItems, "idle": ScaleIdle}


def load_spec(spec_data: Dict[str, Any]) -> ClusterSpec:
    """it intiliazie a ClusterSpec"""
    c = ClusterSpec(**spec_data)
    strategies = []
    for strategy in c.policy.strategies:
        s = STRATEGIES[strategy["name"]](**strategy)
        strategies.append(s)
    c.policy.strategies = strategies
    return c


def load_cluster_file(yaml_path) -> ClusterFile:
    """It will open a cluster spec file"""
    data = open_yaml(yaml_path)
    clusters = {}
    for k, v in data["clusters"].items():
        spec = load_spec(v)
        clusters[k] = spec
    inventory = data.get("inventory")
    default_cluster = data.get("default_cluster")

    return ClusterFile(
        clusters=clusters, inventory=inventory, default_cluster=default_cluster
    )
