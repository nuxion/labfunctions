from nb_workflows.cluster import Inventory, ProviderSpec
from nb_workflows.cluster.control import ClusterControl, apply_scale_items
from nb_workflows.cluster.inventory import Inventory
from nb_workflows.types.cluster import (
    ClusterFile,
    ClusterPolicy,
    ClusterSpec,
    ClusterState,
    ScaleIdle,
    ScaleItems,
)

from .factories import ClusterStateFactory

i = Inventory()
i.reload("tests/machines_test.yaml")


def test_cluster_control_inventory_init():
    i = Inventory("tests/machines_test.yaml")
    i2 = Inventory()
    assert i.machines
    assert i.volumes
    assert "gce" in i.providers
    assert i._inventory_from.endswith("machines_test.yaml")
    assert i2.machines
    assert i2.volumes
    assert not i2._inventory_from.endswith("machines.yaml")


def test_cluster_control_inventory_machines_by():
    i = Inventory()

    machines = i.machines_by_provider("gce")
    assert machines


def test_inventory_provider():
    i = Inventory()
    p = i.get_provider("gce")
    assert isinstance(p, ProviderSpec)


def test_cluster_control_load():
    clusters = ClusterControl.load_cluster_file("tests/clusters_test.yaml")
    assert isinstance(clusters, ClusterFile)
    assert isinstance(clusters.clusters["local"], ClusterSpec)
    assert isinstance(clusters.clusters["local"].policy, ClusterPolicy)
    assert isinstance(clusters.clusters["local"].policy.strategies[0], ScaleIdle)
    assert clusters.inventory == "tests/machines_test.yaml"


def test_cluster_control_init(redis):
    clusters = ClusterControl.load_cluster_file("tests/clusters_test.yaml")
    inventory = Inventory(clusters.inventory)
    cc = ClusterControl(redis, clusters.clusters["local"], inventory)
    policy = cc.policy

    assert cc.cluster_name == "local"
    assert isinstance(cc.state, ClusterState)
    assert cc.state.agents_n == 0
    assert isinstance(policy, ClusterPolicy)


def test_cluster_control_scale_items_gt():
    state = ClusterStateFactory()
    state.queue_items["default"] = 10
    scale = ScaleItems(qname="default", items_gt=1, increase_by=5)
    new_state = apply_scale_items(state, scale)
    assert id(state) != id(new_state)
    assert new_state.agents_n == state.agents_n + 5


def test_cluster_control_scale_items_lt():
    state = ClusterStateFactory()
    state.queue_items["default"] = 1
    scale = ScaleItems(qname="default", items_gt=10, items_lt=2)
    new_state = apply_scale_items(state, scale)
    assert new_state.agents_n == state.agents_n - 1
    assert len(new_state.agents) < len(state.agents)
