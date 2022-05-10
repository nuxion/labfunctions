import json
import logging
import os
from datetime import datetime, timedelta

from labfunctions import client, defaults, secrets

# from labfunctions.executors import context
# from labfunctions.conf.server_settings import settings
from labfunctions.types import ExecutionNBTask, ExecutionResult

from .nbtask_base import NBTaskDocker


def docker_exec(ctx: ExecutionNBTask) -> ExecutionResult:
    """
    It will get a wfid from the control plane.
    This function runs in RQ Worker from a data plane machine.

    Passing task exec information though serialized as an environment
    variable could be a questionable design decision, checks:
        - https://www.in-ulm.de/~mascheck/various/argmax/
        - and https://stackoverflow.com/questions/1078031/what-is-the-maximum-size-of-a-linux-environment-variable-value
        - and getconf -a | grep ARG_MAX # (value in kib)
    """

    agent_token = os.getenv("NB_AGENT_TOKEN")
    refresh_token = os.getenv("NB_AGENT_REFRESH_TOKEN")
    url_service = os.getenv("NB_WORKFLOW_SERVICE")
    nbclient = client.agent(
        url_service=url_service,
        token=agent_token,
        refresh=refresh_token,
        projectid=ctx.projectid,
    )
    runner = NBTaskDocker(nbclient)
    result = runner.run(ctx)
    if result.error and not os.getenv("DEBUG"):
        runner.register(result)
    return result
    # error_result = context.make_error_result(exec_ctx, elapsed)
    # ag_client.history_register(result)
