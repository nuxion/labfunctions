import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path, PosixPath
from typing import Any, Dict, Union

from rich.console import Console

import docker
from nb_workflows import client, secrets
from nb_workflows.conf import defaults
from nb_workflows.executors import context
from nb_workflows.io import Fileserver

# from nb_workflows.conf.server_settings import settings
from nb_workflows.types import (
    ExecutionNBTask,
    ExecutionResult,
    NBTask,
    ProjectData,
    ScheduleData,
)
from nb_workflows.types.docker import DockerBuildCtx
from nb_workflows.utils import format_bytes


def get_result(
    container: docker.models.containers.Container, timeout=5
) -> Union[Dict[str, Any], None]:
    result = None
    try:
        result = container.wait(timeout=5)
    except Exception:
        pass
    return result


def docker_events(
    container: docker.models.containers.Container, timeout_secs=(60 * 60) * 5, watch=5
):

    console = Console()
    now = datetime.utcnow() - timedelta(minutes=10)
    started = time.time()
    elapsed = 0
    running = True
    while running and elapsed < timeout_secs:
        logs = container.logs(since=now).decode("utf-8").split("\n")
        for log in logs:
            _log = log.strip()
            if _log:
                yield {"type": "log", "data": _log}
        now = datetime.utcnow() - timedelta(seconds=2)

        stats = container.stats(decode=True).__next__()
        mem_usage_bytes = stats["memory_stats"].get("usage", 0)
        mem_max_bytes = stats["memory_stats"].get("max_usage", 0)

        mem = {"mem_usage": mem_usage_bytes, "mem_max": mem_max_bytes}
        yield {"type": "stats", "data": {"mem": mem}}

        result = get_result(container, timeout=watch)
        if result:
            running = False
            return result

        elapsed = time.time() - started
        yield {"type": "log", "data": f"{round(elapsed)} secs elapsed"}
        # console.print(log)


def docker_exec(exec_ctx: ExecutionNBTask, volumes=None):
    """
    It will get a wfid from the control plane.
    This function runs in RQ Worker from a data plane machine.

    Maybe a polemic design decision here is passing task execution information
    serialized as environment variable, checks:

        - https://www.in-ulm.de/~mascheck/various/argmax/
        - and https://stackoverflow.com/questions/1078031/what-is-the-maximum-size-of-a-linux-environment-variable-value
        - and getconf -a | grep ARG_MAX # (value in kib)

    TODO: task result should be review with the HistoryModel for better registration
    of workflows executions.
    """
    # from nb_workflows.qworker import settings

    agent_token = os.getenv("NB_AGENT_TOKEN")
    refresh_token = os.getenv("NB_AGENT_REFRESH_TOKEN")
    url_service = os.getenv("NB_WORKFLOW_SERVICE")

    console = Console()

    _started = time.time()
    docker_client = docker.from_env()
    ag_client = client.agent(
        url_service=url_service,
        token=agent_token,
        refresh=refresh_token,
        projectid=exec_ctx.projectid,
    )

    ag_client.events_publish(exec_ctx.execid, "Starting docker execution")

    priv_key = ag_client.projects_private_key()
    if not priv_key:
        ag_client.logger.error(f"jobdid:{exec_ctx.wfid} private key not found")
        elapsed = time.time() - _started
        result = context.make_error_result(exec_ctx, elapsed)
        ag_client.history_register(result)
        return

    msg = (
        f"jobdid:{exec_ctx.wfid} execid:{exec_ctx.execid} "
        f"Sending to docker: {exec_ctx.docker_name}"
    )
    ag_client.logger.info(msg)
    ag_client.events_publish(exec_ctx.execid, msg)
    try:
        container = docker_client.containers.run(
            exec_ctx.docker_name,
            f"nb exec local",
            environment={
                defaults.PRIVKEY_VAR_NAME: priv_key,
                defaults.EXECUTIONTASK_VAR: json.dumps(exec_ctx.dict()),
                "NB_WORKFLOW_SERVICE": url_service,
                defaults.BASE_PATH_ENV: "/app",
            },
            # remove=True,
            detach=True,
        )
        for evt in docker_events(container, timeout_secs=exec_ctx.timeout):
            # console.print(evt["data"])
            if evt["type"] == "stats":
                _mem = evt["data"]["mem"]["mem_usage"]
                mem = format_bytes(_mem)
                msg = f"Memory used {mem}"
            else:
                msg = evt["data"]
            # ag_client.logger.info(msg)
            console.print(msg)
            ag_client.events_publish(
                exec_ctx.execid, data=evt["data"], event=evt["type"]
            )

        result = get_result(container, timeout=1)
        if not result:
            container.kill()
        container.remove()
        ag_client.events_publish(exec_ctx.execid, data="finished", event="result")

    except docker.errors.ContainerError as e:
        ag_client.logger.error(e.stderr.decode())
        elapsed = time.time() - _started
        result = context.make_error_result(exec_ctx, elapsed)
        ag_client.history_register(result)

    except docker.errors.APIError as e:
        ag_client.logger.error(e)

    ag_client.events_publish(exec_ctx.execid, data="exit", event="control")
