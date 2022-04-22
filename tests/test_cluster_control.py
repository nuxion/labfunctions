import pytest
from pytest_mock import MockerFixture

from nb_workflows.cluster import Inventory, ProviderSpec, get_spec_from_file
from nb_workflows.cluster.cluster_file import load_cluster_file, load_spec
from nb_workflows.cluster.control import ClusterControl, apply_scale_items
from nb_workflows.cluster.inventory import Inventory
from nb_workflows.cluster.shortcuts import create_cluster_control
from nb_workflows.control_plane.register import AgentRegister
from nb_workflows.errors.cluster import ClusterSpecNotFound
from nb_workflows.types.cluster import (
    ClusterFile,
    ClusterPolicy,
    ClusterSpec,
    ClusterState,
    ScaleIdle,
    ScaleItems,
)
from nb_workflows.utils import open_yaml

from .factories import ClusterStateFactory

i = Inventory()
i.reload("tests/machines_test.yaml")


def test_cluster_inventory_init():
    i = Inventory("tests/machines_test.yaml")
    i2 = Inventory()
    assert i.machines
    assert i.volumes
    assert "gce" in i.providers
    assert i._inventory_from.endswith("machines_test.yaml")
    assert i2.machines
    assert i2.volumes
    assert not i2._inventory_from.endswith("machines.yaml")


def test_cluster_inventory_machines_by():
    i = Inventory()

    machines = i.machines_by_provider("local")
    assert machines


def test_cluster_inventory_provider():
    i = Inventory()
    p = i.get_provider("local")
    assert isinstance(p, ProviderSpec)


def test_cluster_file_load():
    clusters = load_cluster_file("tests/clusters_test.yaml")

    assert len(clusters.clusters) == 2
    assert clusters.clusters["external"].network == "non-default"
    assert isinstance(clusters, ClusterFile)
    assert isinstance(clusters.clusters["local"], ClusterSpec)
    assert isinstance(clusters.clusters["local"].policy, ClusterPolicy)
    assert isinstance(clusters.clusters["local"].policy.strategies[0], ScaleIdle)
    assert clusters.inventory == "tests/machines_test.yaml"


def test_cluster_file_load_spec():
    data = open_yaml("tests/clusters_test.yaml")
    spec = load_spec(data["clusters"]["local"])

    assert isinstance(spec, ClusterSpec)
    assert isinstance(spec.policy.strategies[0], ScaleIdle)


def test_cluster_file_get_spec():
    spec = get_spec_from_file("tests/clusters_test.yaml")
    external = get_spec_from_file("tests/clusters_test.yaml", "external")
    with pytest.raises(ClusterSpecNotFound):
        nospec = get_spec_from_file("tests/clusters_test.yaml", "nonexist")

    assert isinstance(spec, ClusterSpec)
    assert isinstance(spec.policy.strategies[0], ScaleIdle)
    assert spec.name == "local"
    assert external.name == "external"


def test_cluster_control_create(mocker: MockerFixture, redis):
    mocker.patch("nb_workflows.cluster.shortcuts.redis.from_url", return_value=redis)
    cc = create_cluster_control("tests/clusters_test.yaml", "redis_url", "local")
    with pytest.raises(ClusterSpecNotFound):
        cc = create_cluster_control("tests/clusters_test.yaml", "sara", "non-exist")
    assert cc.spec.name == "local"


def test_cluster_control_init(redis):
    clusters = load_cluster_file("tests/clusters_test.yaml")
    inventory = Inventory(clusters.inventory)
    are = AgentRegister(redis, "local")
    cc = ClusterControl(are, clusters.clusters["local"], inventory)
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
