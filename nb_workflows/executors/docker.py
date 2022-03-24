import json
import logging
import time
from pathlib import Path, PosixPath

import docker
from nb_workflows import client, secrets
from nb_workflows.build import make_build
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


def builder_executor(projectid, project_zip_route):
    """It's in charge of building docker images from projects"""
    from nb_workflows.qworker import settings

    logger = logging.getLogger(__name__)
    root = Path(settings.BASE_PATH)
    project_dir = root / settings.WORKER_DATA_FOLDER / "build" / projectid
    project_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = project_dir / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    fs = Fileserver(settings.FILESERVER, settings.FILESERVER_BUCKET)
    data = fs.get(project_zip_route)
    zip_name = project_zip_route.split("/")[-1]
    with open(project_dir / zip_name, "wb") as f:
        f.write(data)

    nb_client = client.agent(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=projectid,
    )

    _version = zip_name.split(".")[0].lower()

    pd = nb_client.projects_get()
    docker_tag = context.generate_docker_name(pd, docker_version=_version)
    logger.error(docker_tag)
    make_build(project_dir / zip_name, tag=docker_tag, temp_dir=str(temp_dir))
    # register build


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
    from nb_workflows.qworker import settings

    _started = time.time()
    docker_client = docker.from_env()
    ag_client = client.agent(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=exec_ctx.projectid,
    )
    logger = logging.getLogger(__name__)

    priv_key = ag_client.projects_private_key()
    if not priv_key:
        logger.error(f"jobdid:{exec_ctx.wfid} private key not found")
        elapsed = time.time() - _started
        result = context.make_error_result(exec_ctx, elapsed)
        ag_client.history_register(result)
        return

    logger.info(
        f"jobdid:{exec_ctx.wfid} execid:{exec_ctx.execid} "
        f"Sending to docker: {exec_ctx.docker_name}"
    )
    try:
        logs = docker_client.containers.run(
            exec_ctx.docker_name,
            f"nb exec local",
            environment={
                defaults.PRIVKEY_VAR_NAME: priv_key,
                defaults.EXECUTIONTASK_VAR: json.dumps(exec_ctx.dict()),
                "NB_WORKFLOW_SERVICE": settings.WORKFLOW_SERVICE,
            },
            remove=True,
        )

    except docker.errors.ContainerError as e:
        logger.error(e.stderr.decode())
        elapsed = time.time() - _started
        result = context.make_error_result(exec_ctx, elapsed)
        ag_client.history_register(result)
