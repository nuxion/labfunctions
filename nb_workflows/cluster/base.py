from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from nb_workflows.types.cluster import (
    BlockInstance,
    BlockStorage,
    ExecMachineResult,
    ExecutionMachine,
    NodeInstance,
    NodeRequest,
)


class ProviderSpec(ABC):
    @abstractmethod
    def create_machine(self, node: NodeRequest) -> NodeInstance:
        pass

    @abstractmethod
    def destroy_machine(self, node: Union[str, NodeInstance]):
        pass

    @abstractmethod
    def create_volume(self, disk: BlockStorage) -> BlockInstance:
        pass

    @abstractmethod
    def destroy_volume(self, disk: BlockStorage) -> bool:
        pass

    @abstractmethod
    def attach_volume(self, node: NodeInstance, disk: BlockStorage) -> bool:
        pass

    @abstractmethod
    def detach_volume(self, node: NodeInstance, disk: BlockStorage) -> bool:
        pass

    @abstractmethod
    def deploy(self, node: NodeInstance, ctx: ExecutionMachine) -> Dict[str, Any]:
        pass
