from typing import Optional

from libcloud.compute import base
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider

from nb_workflows.types.cluster import DigitalOceanConf, NodeInstance


def create_driver(conf: Optional[DigitalOceanConf] = None) -> base.NodeDriver:
    DigitalOcean = get_driver(Provider.DIGITAL_OCEAN)
    conf = conf or DigitalOceanConf()

    driver = DigitalOcean(conf.acces_token, api_version="v2")
    return driver


def create_instance(driver: base.NodeDriver, node: NodeInstance):
    pass
