import os
import signal
from pathlib import Path
from typing import Any, Dict, Optional, Union

from nb_workflows.types.cluster import (
    BlockInstance,
    BlockStorage,
    ExecutionMachine,
    NodeInstance,
    NodeRequest,
)
from nb_workflows.utils import (
    execute_cmd_no_block,
    get_external_ip,
    get_internal_ip,
    mkdir_p,
)

from .base import ProviderSpec
from .utils import prepare_agent_cmd


class LocalProvider(ProviderSpec):
    def __init__(self, working_dir: str):
        self.working_dir = Path(working_dir)

    def create_machine(self, node: NodeRequest) -> NodeInstance:
        internal = get_internal_ip()
        external = get_external_ip()
        fp = self.working_dir / node.name
        mkdir_p(fp)
        res = NodeInstance(
            node_id=str(fp),
            node_name=node.name,
            location=node.location,
            private_ips=[internal],
            public_ips=[external],
            main_addr=external,
        )
        return res

    def deploy(self, node: NodeInstance, ctx: ExecutionMachine) -> Dict[str, Any]:

        cmd = prepare_agent_cmd(
            node.main_addr,
            qnames=",".join(ctx.qnames),
            env_file=ctx.agent_env_file,
            workers=ctx.worker_procs,
        )

        result = execute_cmd_no_block(cmd, check=False)
        return {"pid": result.pid}

    def destroy_machine(self, node: Union[NodeInstance, str]):
        # rm dir: self.working_dir / ctx.node.name
        pid = node
        if isinstance(node, NodeInstance):
            pid = node.extra["pid"]
        os.kill(int(pid), signal.SIGINT)

    def create_volume(self, disk: BlockStorage) -> BlockInstance:
        pass

    def destroy_volume(self, disk: BlockStorage) -> bool:
        pass

    def attach_volume(self, node: NodeInstance, disk: BlockStorage) -> bool:
        pass

    def detach_volume(self, node: NodeInstance, disk: BlockStorage) -> bool:
        pass
