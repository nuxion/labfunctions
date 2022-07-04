from datetime import datetime
from functools import partial
from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_random

from labfunctions import client, cluster, log, types
from labfunctions.conf import load_server
from labfunctions.executors import ExecID
from labfunctions.executors.docker_exec import docker_exec
from labfunctions.redis_conn import create_pool
from labfunctions.runtimes.builder import builder_exec
from labfunctions.utils import get_version, run_async, today_string


@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
async def _deploy_agent(
    ctx: cluster.DeployAgentTask,
    *,
    private_key_path: str,
    instance: cluster.types.MachineInstance,
    settings: types.ServerSettings,
) -> cluster.types.SSHResult:
    """Used to deploy an agent into a instance."""

    ip = instance.private_ips[0]
    if ctx.use_public:
        ip = instance.public_ips[0]

    agent_req = cluster.types.AgentRequest(
        machine_ip=ip,
        machine_id=instance.machine_id,
        access_token=settings.AGENT_TOKEN,
        refresh_token=settings.AGENT_REFRESH_TOKEN,
        private_key_path=private_key_path,
        cluster=ctx.cluster_name,
        docker_image=ctx.docker_image,
        docker_version=ctx.docker_version,
        web_redis=settings.WEB_REDIS,
        queue_redis=settings.QUEUE_REDIS,
        control_queue=settings.CONTROL_QUEUE,
        workflow_service=settings.WORKFLOW_SERVICE,
    )
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
    return response


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
    """It creates a machine server into a cluster
    if a deploy agent is passed it will deploy that agent too.
    """
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
        alias=ctx.alias,
    )

    instance = await run_async(create)
    await cc.register_instance(instance, ctx.cluster_name)
    log.server_logger.debug(f"{instance.machine_name} Created")
    if ctx.agent:
        log.server_logger.info(f"Deploying agent into {instance.machine_name}")
        agent_ctx = cluster.DeployAgentTask(
            machine_name=instance.machine_name,
            cluster_name=ctx.cluster_name,
            **ctx.agent.dict(),
        )
        response = await _deploy_agent(
            agent_ctx,
            private_key_path=cc.ssh_key.private_path,
            instance=instance,
            settings=settings,
        )

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
    """Somethings a machine already exist without an agent
    it can be used to deploy that agent ."""
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
    log.server_logger.info(f"Deploying agent into {ctx.machine_name}")
    response = await _deploy_agent(
        ctx,
        private_key_path=cc.ssh_key.private_path,
        instance=instance,
        settings=settings,
    )

    return response.dict()
