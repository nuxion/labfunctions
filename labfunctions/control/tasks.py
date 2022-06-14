from datetime import datetime
from functools import partial
from typing import Any, Dict

from labfunctions import client, log, types
from labfunctions.cluster2 import ClusterControl, CreateRequest, DestroyRequest
from labfunctions.conf import load_server
from labfunctions.executors import ExecID
from labfunctions.executors.docker_exec import docker_exec
from labfunctions.redis_conn import create_pool
from labfunctions.runtimes.builder import builder_exec
from labfunctions.utils import get_version, run_async, today_string


def notebook_dispatcher(data: Dict[str, Any]):
    ctx = types.ExecutionNBTask(**data)
    result = docker_exec(ctx)
    return result.dict()


def workflow_dispatcher(data: Dict[str, Any]):
    ctx = types.ExecutionNBTask(**data)
    ctx.execid = str(ExecID())

    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()
    ctx.params["NOW"] = _now
    ctx.created_at = _now
    ctx.today = today
    result = notebook_dispatcher(ctx.dict())
    return result


def build_dispatcher(data: Dict[str, Any]):
    ctx = types.runtimes.BuildCtx(**data)
    result = builder_exec(ctx)
    return result.dict()


async def create_instance(data: Dict[str, Any]):
    settings = load_server()
    pool = create_pool(settings.WEB_REDIS)
    ctx = CreateRequest(**data)
    cluster = ClusterControl(
        settings.CLUSTER_FILEPATH,
        ssh_user=settings.CLUSTER_SSH_KEY_USER,
        ssh_key_public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        conn=pool,
    )
    log.server_logger.info(f"Creating a machine for cluster {ctx.cluster_name}")
    create = partial(
        cluster.create_instance,
        ctx.cluster_name,
        agent_token=settings.AGENT_TOKEN,
        agent_refresh_token=settings.AGENT_REFRESH_TOKEN,
        do_deploy=ctx.do_deploy,
        use_public=ctx.use_public,
    )

    instance = await run_async(create)
    await cluster.register_instance(instance, ctx.cluster_name)
    log.server_logger.debug(f"{instance.machine_name} Created")

    return instance.dict()


async def destroy_instance(data: Dict[str, Any]):
    settings = load_server()
    pool = create_pool(settings.WEB_REDIS)
    ctx = DestroyRequest(**data)
    cluster = ClusterControl(
        settings.CLUSTER_FILEPATH,
        ssh_user=settings.CLUSTER_SSH_KEY_USER,
        ssh_key_public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        conn=pool,
    )
    log.server_logger.info(
        f"Destroying {ctx.machine_name} for cluster {ctx.cluster_name}"
    )

    destroy = partial(
        cluster.destroy_instance, ctx.machine_name, cluster_name=ctx.cluster_name
    )

    await run_async(destroy)
    await cluster.unregister_instance(ctx.machine_name, ctx.cluster_name)
    log.server_logger.debug(f"{ctx.machine_name} destroyed")
