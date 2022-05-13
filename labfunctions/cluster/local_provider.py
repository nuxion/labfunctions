import glob
import json
import os
import shutil
import signal
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseSettings

from labfunctions.types.machine import (
    BlockInstance,
    BlockStorage,
    ExecutionMachine,
    MachineInstance,
    MachineRequest,
)
from labfunctions.utils import (
    execute_cmd_no_block,
    get_external_ip,
    get_internal_ip,
    mkdir_p,
)

from .base import ProviderSpec


class LCConf(BaseSettings):
    working_dir: str

    class Config:
        env_prefix = "LF_LCL_"


class LocalProvider(ProviderSpec):
    def __init__(self, conf: Optional[LCConf] = None):
        self.conf = conf or LCConf()
        self.working_dir = Path(self.conf.working_dir)

    def create_machine(self, node: MachineRequest) -> MachineInstance:
        internal = get_internal_ip()
        external = get_external_ip()
        fp = self.working_dir / node.name
        mkdir_p(fp)

        res = MachineInstance(
            machine_id=f"/local/{node.location}/{node.name}",
            machine_name=node.name,
            location=node.location,
            private_ips=[internal],
            public_ips=[external],
            labels=node.labels,
        )
        with open(fp / "machine.json", "w") as f:
            f.write(res.json())
        return res

    def list_machines(
        self, location: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[MachineInstance]:

        machines = []
        for node in glob.glob(f"{self.working_dir}/*/machine.json"):
            with open(node, "r") as f:
                data = f.read()
                obj = json.loads(data)
                instance = MachineInstance(**obj)
                machines.append(instance)

        return machines

    def destroy_machine(self, node: Union[MachineInstance, str]):
        # rm dir: self.working_dir / ctx.node.name
        node_dir = node
        if isinstance(node, MachineInstance):
            node_dir = node.machine_name

        shutil.rmtree(str(self.working_dir / node_dir))

    def create_volume(self, disk: BlockStorage) -> BlockInstance:
        pass

    def destroy_volume(self, disk: Union[str, BlockStorage]) -> bool:
        pass

    def attach_volume(self, node: MachineInstance, disk: BlockStorage) -> bool:
        pass

    def detach_volume(self, node: MachineInstance, disk: BlockStorage) -> bool:
        pass
