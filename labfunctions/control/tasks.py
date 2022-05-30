from typing import Any, Dict

from labfunctions import types
from labfunctions.executors.docker_exec import docker_exec
from labfunctions.runtimes.builder import builder_exec


def notebook_dispatcher(data: Dict[str, Any]):
    ctx = types.ExecutionNBTask(**data)
    result = docker_exec(ctx)
    return result.dict()


def build_dispatcher(data: Dict[str, Any]):
    ctx = types.runtimes.BuildCtx(**data)
    result = builder_exec(ctx)
    return result.dict()
