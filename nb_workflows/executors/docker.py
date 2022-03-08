import json
import logging
import time
from pathlib import Path, PosixPath

import docker

from nb_workflows import client, secrets
from nb_workflows.build import generate_docker_name, make_build
from nb_workflows.conf import defaults
from nb_workflows.io import Fileserver

# from nb_workflows.conf.server_settings import settings
from nb_workflows.types import ExecutionResult, NBTask, ProjectData, ScheduleData

from .utils import create_exec_ctx


def builder_executor(projectid, project_zip_route):
    """It's in charge of building docker images from projects"""
    from nb_workflows.qworker import settings

    root = Path(settings.BASE_PATH)
    project_dir = root / settings.WORKER_DATA_FOLDER / "build" / projectid
    project_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = project_dir / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    fs = Fileserver(settings.FILESERVER)
    data = fs.get(project_zip_route)
    zip_name = project_zip_route.split("/")[-1]
    with open(project_dir / zip_name, "wb") as f:
        f.write(data)

    nb_client = client.minimal_client(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=projectid,
    )

    _version = zip_name.split(".")[0].lower()

    pd = nb_client.projects_get()
    docker_tag = generate_docker_name(pd, docker_version=_version)
    make_build(project_dir / zip_name, tag=docker_tag, temp_dir=str(temp_dir))


def docker_exec(projectid, priv_key, jobid):
    """
    It will get a jobid from the control plane.
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
    nb_client = client.minimal_client(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=projectid,
    )
    logger = logging.getLogger(__name__)

    try:
        wd = nb_client.workflows_get(jobid)
        pd = nb_client.projects_get()
        task = NBTask(**wd.job_detail)
        if task.schedule:
            task.schedule = ScheduleData(**wd.job_detail["schedule"])
        if wd and wd.enabled and pd:
            ctx = create_exec_ctx(projectid, jobid, task)
            docker_name = generate_docker_name(pd, task.docker_version)
            logger.info(
                f"jobdid:{ctx.jobid} execid:{ctx.executionid} Sending to docker:{docker_name}"
            )

            logs = docker_client.containers.run(
                docker_name,
                f"nb exec",
                environment={
                    defaults.PRIVKEY_VAR_NAME: priv_key,
                    defaults.EXECUTIONTASK_VAR: json.dumps(ctx.dict()),
                    "NB_WORKFLOW_SERVICE": "http://192.168.88.150:8000",
                },
            )

        elif not wd:
            logger.warning(f"jobdid:{jobid} Not found")
        elif not wd.enabled:
            logger.warning(f"jobdid:{jobid} disabled")
        else:
            logger.warning(f"jobdid:{jobid} project not found")

    except docker.errors.ContainerError as e:
        logger.error(e.stderr.decode())
        elapsed = time.time() - _started
        result = ExecutionResult(
            jobid=ctx.jobid,
            executionid=ctx.executionid,
            projectid=ctx.projectid,
            name=ctx.nb_name,
            params=ctx.params,
            input_=ctx.pm_input,
            output_dir=ctx.output_dir,
            output_name=ctx.output_name,
            error_dir=ctx.error_dir,
            error=True,
            elapsed_secs=round(elapsed, 2),
            created_at=ctx.created_at,
        )
        nb_client.history_register(result)

    except Exception as e:
        logger.error(f"jobid:{jobid} Failed {e}")

    return None
