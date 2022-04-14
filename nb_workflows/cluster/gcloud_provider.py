import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from libcloud.compute.base import Node, NodeLocation
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from pydantic import BaseSettings

from nb_workflows.types.cluster import (
    BlockInstance,
    BlockStorage,
    ExecMachineResult,
    ExecutionMachine,
    NodeInstance,
    NodeRequest,
)
from nb_workflows.utils import run_sync

from . import ssh
from .base import ProviderSpec
from .utils import prepare_docker_cmd


class GConf(BaseSettings):
    service_account: str
    project: str
    pem_file: Optional[str] = None
    datacenter: Optional[str] = None
    credential_file: Optional[str] = None

    class Config:
        env_prefix = "NB_GCE_"


def get_gce_driver():
    GCE = get_driver(Provider.GCE)
    return GCE


def generic_zone(name, driver) -> NodeLocation:
    return NodeLocation(id=None, name=name, country=None, driver=driver)


class GCEProvider(ProviderSpec):
    def __init__(self, conf: Optional[GConf] = None):
        self.conf = conf or GConf()
        G = get_gce_driver()
        # _env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        # if _env_creds:
        #     conf.credential_file = _env_creds

        self.driver = G(
            self.conf.service_account,
            key=self.conf.pem_file,
            project=self.conf.project,
            datacenter=self.conf.datacenter,
        )

    def _get_volume(self, vol_name):
        volumes = [v for v in self.driver.list_volumes() if v.name == vol_name]
        if len(volumes) > 0:
            return volumes[0]
        return None

    def _get_volumes_to_attach(self, volumes: List[BlockStorage]):
        to_attach = []
        for vol in volumes:
            v = self._get_volume(vol.name)
            if v:
                to_attach.append(v)
        if to_attach:
            return to_attach
        return None

    def create_machine(self, node: NodeRequest) -> NodeInstance:
        metadata = {
            "items": [
                {"key": "ssh-keys", "value": f"{node.ssh_user}: {node.ssh_public_cert}"}
            ]
        }
        if node.volumes:
            volumes = self._get_volumes_to_attach(node.volumes)

        instance = self.driver.create_node(
            node.name,
            size=node.size,
            image=node.image,
            location=node.location,
            ex_network=node.network,
            ex_metadata=metadata,
            ex_tags=node.tags,
        )
        if volumes:
            for v in volumes:
                self.driver.attach_volume(instance, v)

        res = NodeInstance(
            node_id=instance.id,
            node_name=node.name,
            location=node.location,
            main_addr=instance.private_ips[0],
            private_ips=instance.private_ips,
            public_ips=instance.public_ips,
            extra=instance.extra,
        )
        return res

    def destroy_machine(self, node: Union[str, NodeInstance]):
        name = node
        if isinstance(node, NodeInstance):
            name = node.node_name
        nodes = self.driver.list_nodes()
        _node = [n for n in nodes if n.name == name][0]
        _node.destroy()

    def deploy(self, node: NodeInstance, ctx: ExecutionMachine) -> Dict[str, Any]:
        key = ctx.ssh_key.private_path
        run_sync(
            ssh.scp_from_local,
            remote_addr=node.main_addr,
            remote_dir=ctx.agent_homedir,
            local_file=ctx.agent_env_file,
            keys=[key],
        )

        if ctx.node.volumes:
            v = ctx.node.volumes[0]
            mount_cmd = (
                f"sudo mkdir -p {v.mount} && "
                f"sudo mount /dev/sdb  {v.mount} && "
                f"sudo mkdir -p {v.mount}/data && "
                f"sudo chown {ctx.docker_uid}:{ctx.docker_gid} {v.mount}/data"
            )
            run_sync(ssh.run_cmd, node.main_addr, mount_cmd, keys=[key])

        cmd = prepare_docker_cmd(
            node.main_addr,
            qnames=",".join(ctx.qnames),
            docker_image=ctx.docker_image,
            env_file=f"{ctx.agent_homedir}/{ctx.agent_env_file}",
            workers=ctx.worker_procs,
            docker_version=ctx.docker_version,
        )

        result = run_sync(ssh.run_cmd, node.main_addr, cmd, keys=[key])
        r = {"result": result}
        return r

    def create_volume(self, disk: BlockStorage) -> BlockInstance:
        vol = self.driver.create_volume(
            disk.size,
            disk.name,
            location=disk.location,
            snapshot=disk.snapshot,
            ex_disk_type=disk.kind,
        )
        block = BlockInstance(id=vol.id, **disk.dict())
        block.extra = vol.extra
        return block

    def destroy_volume(self, disk: BlockStorage) -> bool:
        vol = [v for v in self.driver.list_volumes() if v.name == disk.name]
        rsp = self.driver.destroy_volume(vol)
        return rsp

    def attach_volume(self, node: NodeInstance, disk: BlockStorage):
        _node = [n for n in self.driver.list_nodes() if n.name == node.node_name][0]
        vol = [v for v in self.driver.list_volumes() if v.name == disk.name]

        res = self.driver.attach_volume(_node, vol)
        return res

    def detach_volume(self, node: NodeInstance, disk: BlockStorage) -> bool:
        _node = [n for n in self.driver.list_nodes() if n.name == node.node_name][0]
        vol = [v for v in self.driver.list_volumes() if v.name == disk.name]
        res = self.driver.detach_volume(vol, _node)
        return res
