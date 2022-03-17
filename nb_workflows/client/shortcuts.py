import getpass
import json
import os
from pathlib import Path
from typing import Union

import httpx

from nb_workflows.conf import defaults, load_client
from nb_workflows.conf.types import ClientSettings
from nb_workflows.executors import context
from nb_workflows.io import MemoryStore
from nb_workflows.types import ExecutionNBTask, NBTask, ProjectData, ScheduleData
from nb_workflows.utils import get_parent_folder, secure_filename

from .agent import AgentClient
from .diskclient import DiskClient
from .nbclient import NBClient
from .state import WorkflowsState
from .state import from_file as ws_from_file
from .types import Credentials
from .utils import (
    _example_task,
    get_credentials_disk,
    login_cli,
    validate_credentials_local,
)


def normalize_name(name: str) -> str:
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def ask_project_name() -> str:
    parent = get_parent_folder()
    _default = normalize_name(parent)
    project_name = str(
        input(f"Write a name for this project (default: {_default}): ") or _default
    )
    name = normalize_name(project_name)
    print("The final name for the project will be: ", name)
    return name


def init(url_service, example=True, version="0.2.0") -> DiskClient:

    settings = load_client()
    tasks = None
    if example:
        task = _example_task()
        tasks = {task.alias: task}

    creds = login_cli(url_service)

    projectid = settings.PROJECTID
    name = settings.PROJECT_NAME

    if not projectid:
        name = ask_project_name()
        rsp = httpx.get(f"{settings.WORKFLOW_SERVICE}/projects/_generateid")
        projectid = rsp.json()["projectid"]

    pd = ProjectData(name=name, projectid=projectid)
    wf_state = WorkflowsState(pd, workflows=tasks, version=version)

    _client = DiskClient(
        url_service,
        projectid=projectid,
        creds=creds,
        wf_state=wf_state,
        version=version,
    )

    create = str(input("Create project in the server? (Y/n): ") or "y")
    if create.lower() == "y":
        _client.projects_create()
    _client.write()

    return _client


def nb_from_settings() -> NBClient:
    settings = load_client()
    tasks = None
    creds = Credentials(
        access_token=settings.CLIENT_TOKEN,
        refresh_token=settings.CLIENT_REFRESH_TOKEN,
    )
    pd = ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID)

    wf_state = WorkflowsState(pd)
    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        projectid=settings.PROJECTID,
        wf_state=wf_state,
    )


def nb_from_settings_agent() -> NBClient:
    tasks = None
    settings = load_client()
    creds = Credentials(
        access_token=settings.AGENT_TOKEN,
        refresh_token=settings.AGENT_REFRESH_TOKEN,
    )
    pd = ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID)

    wf_state = WorkflowsState(pd)

    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        projectid=settings.PROJECTID,
        wf_state=wf_state,
    )


def from_file(
    filepath, url_service=None, home_dir=defaults.CLIENT_HOME_DIR
) -> DiskClient:
    """intialize a py:class:`nb_workflows.client.diskclient.DiskClient`
    using data from local like workflows.yaml.
    """

    settings = load_client()
    wf_state = ws_from_file(filepath)
    creds = get_credentials_disk(home_dir)
    if not creds:
        creds = login_cli(url_service, home_dir)

    return DiskClient(
        url_service=settings.WORKFLOW_SERVICE,
        projectid=wf_state.project.projectid,
        creds=creds,
        wf_state=wf_state,
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
        # store_creds=store_creds,
        projectid=projectid,
    )


def agent_client(
    url_service, token, refresh, projectid, store_creds=False
) -> AgentClient:
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
    return AgentClient(
        url_service=url_service,
        creds=creds,
        projectid=projectid,
    )


def create_ctx(wfid=None) -> ExecutionNBTask:
    ctx_str = os.getenv(defaults.EXECUTIONTASK_VAR)
    if ctx_str:
        exec_ctx = ExecutionNBTask(**json.loads(ctx_str))
    else:
        execid = context.ExecID()
        wf = NBClient.read("workflows.yaml")
        pd = wf.project
        pd.username = "dummy"
        wf_data = None
        if wfid:
            for w in wf.workflows:
                if w.wfid == wfid:
                    wf_data = w
        else:
            # TODO: dumy nb_name
            wf_data = NBTask(nb_name="test", params={})

        exec_ctx = context.create_notebook_ctx(pd, wf_data, execid.pure())
    return exec_ctx
