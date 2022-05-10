from typing import Optional

import httpx
from libcloud.compute import base
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from pydantic import BaseModel, BaseSettings

from labfunctions.types.cluster import DigitalOceanConf, NodeInstance


class DigitalOceanConf(BaseSettings):
    access_token: str
    api_version: str = "v2"

    class Config:
        env_prefix = "NB_DO_"


DO_URL = "https://api.digitalocean.com"

metadata = "#cloud-config\nusers:\n  - default\n  - name: {}\n    sudo: ALL=(ALL) NOPASSWD:ALL\n    groups: sudo\n    ssh_authorized_keys:\n      - {}\n"


def create_driver(conf: Optional[DigitalOceanConf] = None) -> base.NodeDriver:
    DigitalOcean = get_driver(Provider.DIGITAL_OCEAN)
    conf = conf or DigitalOceanConf()

    driver = DigitalOcean(conf.access_token, api_version="v2")
    return driver


def create_instance(driver: base.NodeDriver, node: NodeInstance):
    _meta = metadata.format(node.ssh_user, node.ssh_public)
    ex_create_attr = {}
    if node.tags:
        ex_create_attr.update({"tags": node.tags})

    if node.network and node.network != "default":
        ex_create_attr.update({"vpc_uuid": node.network})

    instance = driver.create_node(
        node.name,
        size=node.size,
        image=node.image,
        location=node.location,
        ex_user_data=_meta,
        ex_create_attr=ex_create_attr,
    )
    return instance


def create_driver2(conf: Optional[DigitalOceanConf] = None):

    conf = conf or DigitalOceanConf()
    url = f"{DO_URL}/{conf.api_version}"
    print(url)
    driver = httpx.Client(
        base_url=url,
        headers={"Authorization": f"Bearer {conf.access_token}"},
        timeout=60,
    )
    return driver


def create_instance2(driver, node: NodeInstance, fingerprint):
    """
    https://docs.digitalocean.com/reference/api/api-reference/#operation/create_droplet
    {

        "name": "example.com",
        "region": "nyc3",
        "size": "s-1vcpu-1gb",
        "image": "ubuntu-20-04-x64",
        "ssh_keys":

        [

            289794,
            "3b:16:e4:bf:8b:00:8b:b8:59:8c:a9:d3:f0:19:fa:45"

        ],
        "backups": true,
        "ipv6": true,
        "monitoring": true,
        "tags":

        [
            "env:prod",
            "web"
        ],
        "user_data": "#cloud-config\nruncmd:\n - touch /test.txt\n",
        "vpc_uuid": "760e09ef-dc84-11e8-981e-3cfdfeaae000"

    }
    """

    _meta = metadata.format(node.ssh_user, node.ssh_public)
    data = dict(
        name=node.name,
        region=node.location,
        size=node.size,
        image=node.image,
        ssh_keys=[fingerprint],
        user_data=_meta,
    )
    rsp = driver.post("/droplets", json=data)
    return rsp
