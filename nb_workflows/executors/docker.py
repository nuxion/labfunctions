import json
from pathlib import Path, PosixPath

import docker

from nb_workflows import client, secrets
from nb_workflows.build import build
from nb_workflows.conf import defaults
from nb_workflows.io import Fileserver

# from nb_workflows.conf.server_settings import settings
from nb_workflows.types import NBTask, ProjectData, ScheduleData

from .utils import create_exec_ctx


def generate_docker_name(pd: ProjectData, docker_version: str):
    return f"{pd.username}/{pd.name}:{docker_version}"


def before_exec(projectid) -> PosixPath:
    from nb_workflows.qworker import settings

    root = Path(settings.BASE_PATH)
    worker_folder = root / settings.WORKER_DATA_FOLDER
    runtimes_folder = worker_folder / settings.DOCKER_RUNTIMES
    project_folder = runtimes_folder / projectid
    project_folder.mkdir(parents=True, exist_ok=True)
    return project_folder


def after_exec():
    pass


def build_dockerimage(projectid, project_zip_route):
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
    build(project_dir / zip_name, temp_dir=str(temp_dir), tag=docker_tag)


def docker_exec(projectid, priv_key, jobid):
    """
    Checks: https://www.in-ulm.de/~mascheck/various/argmax/
    and: https://stackoverflow.com/questions/1078031/what-is-the-maximum-size-of-a-linux-environment-variable-value
    and: getconf -a | grep ARG_MAX # (value in kib)
    """
    # before_exec(projectid)
    from nb_workflows.qworker import settings

    docker_client = docker.from_env()
    nb_client = client.minimal_client(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=projectid,
    )

    try:
        wd = nb_client.workflows_get(jobid)
        pd = nb_client.projects_get()
        task = NBTask(**wd.job_detail)
        if task.schedule:
            task.schedule = ScheduleData(**wd.job_detail["schedule"])
        if wd and wd.enabled and pd:
            ctx = create_exec_ctx(projectid, jobid, task)
            docker_name = generate_docker_name(pd, task.docker_version)

            docker_client.containers.run(
                docker_name,
                f"nb exec",
                environment={
                    defaults.PRIVKEY_VAR_NAME: priv_key,
                    defaults.EXECUTIONTASK_VAR: json.dumps(ctx.dict()),
                },
            )
        elif not wd:
            print(f"{jobid} deleted...")
        else:
            print(f"{jobid} not enabled")
    except KeyError:
        print("Invalid credentials")
    except TypeError:
        print("Somenthing went wrong")
    return None
