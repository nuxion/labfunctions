from typing import List, Optional, Union

from libcloud.compute import base
from libcloud.compute.drivers.gce import GCENodeDriver, GCENodeImage, GCENodeSize
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider

from nb_workflows.types.cluster import GoogleConf, NodeInstance


def get_image(img_name, images: List[GCENodeImage]) -> Union[GCENodeImage, None]:
    img = [i for i in images if i.name == img_name]
    if not img:
        return None
    return img[0]


def get_size(size_name, sizes: List[GCENodeSize]) -> Union[GCENodeSize, None]:
    size = [s for s in sizes if s.name == size_name]
    if not size:
        return None
    return size[0]


def create_driver(conf: Optional[GoogleConf] = None) -> GCENodeDriver:
    ComputeEngine = get_driver(Provider.GCE)
    conf = conf or GoogleConf()
    driver: GCENodeDriver = ComputeEngine(
        conf.service_account,
        conf.pem_file,
        project=conf.project,
        datacenter=conf.datacenter,
    )
    return driver


def create_instance(driver: GCENodeDriver, node: NodeInstance) -> base.Node:
    metadata = {
        "items": [{"key": "ssh-keys", "value": f"{node.ssh_user}: {node.ssh_public}"}]
    }
    instance = driver.create_node(
        node.name,
        size=node.size,
        image=node.image,
        location=node.location,
        ex_network=node.network,
        ex_metadata=metadata,
        ex_tags=node.tags,
    )
    return instance


def destroy_instance(driver: GCENodeDriver, name):
    nodes = driver.list_nodes()
    node = [n for n in nodes if n.name == name][0]
    driver.destroy_node(node)
