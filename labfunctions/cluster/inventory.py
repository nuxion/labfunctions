from typing import Dict, List, Optional

from labfunctions.types.machine import BlockStorage, MachineOrm, SSHKey
from labfunctions.utils import Singleton, get_class, open_yaml, pkg_route

from .base import ProviderSpec


class Inventory(metaclass=Singleton):
    def __init__(self, inventory_path: Optional[str] = None):
        path = inventory_path or f"{pkg_route()}/conf/machines.yaml"
        data = open_yaml(path)
        self._inventory_from = path
        self.machines: Dict[str, MachineOrm] = {
            k: MachineOrm(**m) for k, m in data["machines"].items()
        }
        self.volumes: Dict[str, BlockStorage] = {
            k: BlockStorage(**v) for k, v in data["volumes"].items()
        }
        self.providers: Dict[str, str] = data["providers"]

    def reload(self, inventory_path):
        path = inventory_path
        data = open_yaml(path)
        self._inventory_from = path
        self.machines: Dict[str, MachineOrm] = {
            k: MachineOrm(**m) for k, m in data["machines"].items()
        }
        self.volumes: Dict[str, BlockStorage] = {
            k: BlockStorage(**v) for k, v in data["volumes"].items()
        }
        self.providers: Dict[str, str] = data["providers"]

    def machines_by_provider(self, provider: str) -> List[MachineOrm]:
        machines = []
        for k, m in self.machines.items():
            if m.provider == provider:
                machines.append(m)
        return machines

    def get_provider(self, name, *args, **kwargs) -> ProviderSpec:
        prov: ProviderSpec = get_class(self.providers[name])(*args, **kwargs)
        return prov
