from datetime import datetime
from functools import partial
from typing import Any, Dict

from labfunctions import client, cluster, log, types
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
    ctx = cluster.CreateRequest(**data)
    cc = cluster.ClusterControl(
        settings.CLUSTER_FILEPATH,
        ssh_user=settings.CLUSTER_SSH_KEY_USER,
        ssh_key_public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        conn=pool,
    )
    log.server_logger.info(f"Creating a machine for cluster {ctx.cluster_name}")

    create = partial(
        cc.create_instance,
        ctx.cluster_name,
        agent_token=settings.AGENT_TOKEN,
        agent_refresh_token=settings.AGENT_REFRESH_TOKEN,
        deploy_agent=ctx.agent,
    )

    instance = await run_async(create)
    await cc.register_instance(instance, ctx.cluster_name)
    log.server_logger.debug(f"{instance.machine_name} Created")

    return instance.dict()


async def destroy_instance(data: Dict[str, Any]):
    settings = load_server()
    pool = create_pool(settings.WEB_REDIS)
    ctx = cluster.DestroyRequest(**data)
    cc = cluster.ClusterControl(
        settings.CLUSTER_FILEPATH,
        ssh_user=settings.CLUSTER_SSH_KEY_USER,
        ssh_key_public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        conn=pool,
    )
    log.server_logger.info(
        f"Destroying {ctx.machine_name} for cluster {ctx.cluster_name}"
    )

    destroy = partial(
        cc.destroy_instance, ctx.machine_name, cluster_name=ctx.cluster_name
    )

    await run_async(destroy)
    await cc.unregister_instance(ctx.machine_name, ctx.cluster_name)
    log.server_logger.debug(f"{ctx.machine_name} destroyed")


async def deploy_agent(data: Dict[str, Any]):
    settings = load_server()
    ctx = cluster.DeployAgentTask(**data)
    pool = create_pool(settings.WEB_REDIS)
    cc = cluster.ClusterControl(
        settings.CLUSTER_FILEPATH,
        ssh_user=settings.CLUSTER_SSH_KEY_USER,
        ssh_key_public_path=settings.CLUSTER_SSH_PUBLIC_KEY,
        conn=pool,
    )
    instance = await cc.get_instance(ctx.machine_name)
    ip = instance.private_ips[0]
    if ctx.use_public:
        ip = instance.public_ips[0]

    agent_req = cluster.types.AgentRequest(
        machine_ip=ip,
        machine_id=instance.machine_id,
        access_token=settings.AGENT_TOKEN,
        refresh_token=settings.AGENT_REFRESH_TOKEN,
        private_key_path=cc.ssh_key.private_path,
        cluster=ctx.cluster_name,
        docker_image=ctx.agent_docker_image,
        docker_version=ctx.agent_docker_version,
        web_redis=settings.WEB_REDIS,
        queue_redis=settings.QUEUE_REDIS,
        control_queue=settings.CONTROL_QUEUE,
        workflow_service=settings.WORKFLOW_SERVICE,
    )
    log.server_logger.info(f"Deploying agent into {ctx.machine_name}")
    # await run_async(deploy.agent, agent_req)
    res = await cluster.deploy.agent_async(agent_req)
    response = cluster.types.SSHResult(
        command=res.command,
        return_code=res.returncode,
        stderror=res.stderr,
        stdout=res.stdout,
    )
    if response.return_code != 0:
        log.server_logger.error(f"Agent failed for {ctx.machine_name}")
        log.server_logger.error(response.stderror)
    else:
        log.server_logger.info(f"Agent deployed into {ctx.machine_name}")

    return response.dict()
