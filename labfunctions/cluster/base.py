from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from labfunctions.types.machine import (
    BlockInstance,
    BlockStorage,
    ExecMachineResult,
    ExecutionMachine,
    MachineInstance,
    MachineRequest,
)


class ProviderSpec(ABC):
    @abstractmethod
    def create_machine(self, node: MachineRequest) -> MachineInstance:
        pass

    @abstractmethod
    def destroy_machine(self, node: Union[str, MachineInstance]):
        pass

    @abstractmethod
    def list_machines(
        self, location: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[MachineInstance]:
        pass

    @abstractmethod
    def create_volume(self, disk: BlockStorage) -> BlockInstance:
        pass

    @abstractmethod
    def destroy_volume(self, disk: Union[str, BlockStorage]) -> bool:
        pass

    @abstractmethod
    def attach_volume(self, node: MachineInstance, disk: BlockStorage) -> bool:
        pass

    @abstractmethod
    def detach_volume(self, node: MachineInstance, disk: BlockStorage) -> bool:
        pass
