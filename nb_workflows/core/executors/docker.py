from pathlib import Path, PosixPath

import docker

from nb_workflows import client, secrets
from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.core.entities import NBTask, ProjectData, ScheduleData


def before_exec(projectid) -> PosixPath:
    root = Path(settings.BASE_PATH)
    worker_folder = root / settings.WORKER_DATA_FOLDER
    runtimes_folder = worker_folder / settings.DOCKER_RUNTIMES
    project_folder = runtimes_folder / projectid
    project_folder.mkdir(parents=True, exist_ok=True)
    return project_folder


def after_exec():
    pass


def generate_docker_name(task: NBTask, pd: ProjectData):
    return f"{pd.username}/{pd.name}:{task.docker_version}"


def docker_exec(projectid, priv_key, jobid):
    # before_exec(projectid)

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
            docker_name = generate_docker_name(task, pd)

            docker_client.containers.run(
                docker_name,
                f"nb wf exec -J {jobid}",
                environment={defaults.PRIVKEY_VAR_NAME: priv_key},
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
