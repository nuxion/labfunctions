import getpass
import json
from pathlib import Path
from typing import Union

import httpx

from nb_workflows.conf import load_client
from nb_workflows.core.entities import NBTask, ProjectData, ScheduleData
from nb_workflows.core.managers import projects
from nb_workflows.io import MemoryStore

from .agent import AgentClient
from .nbclient import NBClient
from .types import Credentials
from .utils import _example_task, get_credentials_disk, login_cli


def init(url_service, example=True, version="0.1.0") -> NBClient:

    settings = load_client()
    tasks = None
    if example:
        tasks = [_example_task()]

    creds = login_cli(url_service)
    projectid = settings.PROJECTID
    name = settings.PROJECT_NAME
    if not projectid:
        name = projects.ask_project_name()
        rsp = httpx.get(f"{settings.WORKFLOW_SERVICE}/projects/_generateid")
        projectid = rsp.json()["projectid"]

    # wf_file = create_empty_workfile(projectid, name, tasks=tasks)

    nb_client = NBClient(
        creds=creds,
        store_creds=True,
        url_service=url_service,
        projectid=projectid,
        project=ProjectData(name=name, projectid=projectid),
        workflows=tasks,
        version=version,
    )

    create = str(input("Create project in the server? (Y/n): ") or "y")
    if create.lower() == "y":
        nb_client.projects_create()
    nb_client.write()

    return nb_client


def nb_from_settings() -> NBClient:
    settings = load_client()
    tasks = None
    creds = Credentials(
        access_token=settings.CLIENT_TOKEN,
        refresh_token=settings.CLIENT_REFRESH_TOKEN,
    )

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        projectid=settings.PROJECTID,
        project=ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID),
    )


def nb_from_file(filepath, url_service) -> NBClient:
    settings = load_client()
    wf = NBClient.read(filepath)
    # tasks = [wf.workflows[k] for k in wf.workflows.keys()]
    creds = get_credentials_disk()
    if not creds:
        creds = login_cli(url_service)

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        projectid=wf.project.projectid,
        creds=creds,
        store_creds=True,
        project=wf.project,
        workflows=wf.workflows,
    )


def minimal_client(
    url_service, token, refresh, projectid, store_creds=False
) -> NBClient:
    """A shortcut to intialize :class:`nb_workflows.client.NBClient`

    Usually, it is used in each machine running a agent (data plane),
    and is used to communicates with server for workflows task
    preparations.

    TODO: in the future agent use case should be treat apart. Right now
    if the credential env variable is outdated, then
    it will be allways refreshing their token.

    Workaround #1: extend expire time for services like tokens
    Workaround #2: manage a shared store like
    store_creds_disk with redis instead
    Workaround #3: Inject crendentials with the task.


    :param url_service: WORKFLOWS_SERVICE url
    :param token: access_token
    :param refresh: refresh_token
    :param projectid: projectid
    """
    creds = Credentials(access_token=token, refresh_token=refresh)
    return NBClient(
        url_service=url_service,
        creds=creds,
        store_creds=store_creds,
        projectid=projectid,
    )
