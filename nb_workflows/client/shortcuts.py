import getpass
import json
import os
from pathlib import Path
from typing import Optional, Union

import httpx

from nb_workflows import defaults, secrets
from nb_workflows.conf import load_client
from nb_workflows.io import MemoryStore
from nb_workflows.types import (
    ClientSettings,
    ExecutionNBTask,
    NBTask,
    ProjectData,
    ScheduleData,
)
from nb_workflows.utils import get_parent_folder, secure_filename

from .diskclient import DiskClient
from .nbclient import NBClient
from .state import WorkflowsState
from .state import from_file as ws_from_file
from .types import Credentials
from .utils import _example_task, get_credentials_disk, validate_credentials_local


def _load_creds(settings: ClientSettings, nbvars) -> Union[Credentials, None]:
    creds = None
    at = nbvars.get("AGENT_TOKEN", settings.AGENT_TOKEN)
    rt = nbvars.get("AGENT_REFRESH_TOKEN", settings.AGENT_REFRESH_TOKEN)
    if at and rt:
        creds = Credentials(access_token=at, refresh_token=rt)
    return creds


def normalize_name(name: str) -> str:
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def from_file(
    filepath="workflows.yaml", url_service=None, home_dir=defaults.CLIENT_HOME_DIR
) -> DiskClient:
    """intialize a py:class:`nb_workflows.client.diskclient.DiskClient`
    using data from local like workflows.yaml.
    """

    settings = load_client()
    wf_state = ws_from_file(filepath)
    wf_service = url_service or settings.WORKFLOW_SERVICE
    # creds = get_credentials_disk(home_dir)
    # if not creds:
    #    creds = login_cli(url_service, home_dir)
    dc = DiskClient(
        url_service=wf_service,
        wf_state=wf_state,
    )
    if not os.environ.get("DEBUG"):
        try:
            dc.logincli()
        except httpx.ConnectError:
            print("No connection with server")
    return dc


def from_env(settings: Optional[ClientSettings] = None) -> NBClient:
    """Creates a client using the settings module and environment variables"""
    if not settings:
        settings = load_client()
    nbvars = secrets.load(settings.BASE_PATH)

    tasks = None
    creds = _load_creds(settings, nbvars)

    pd = ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID)

    wf_state = WorkflowsState(pd)
    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        wf_state=wf_state,
    )


def agent(url_service, token, refresh, projectid) -> NBClient:
    """A shortcut to intialize

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
    wf = WorkflowsState(ProjectData(name="", projectid=projectid))
    creds = Credentials(access_token=token, refresh_token=refresh)
    return NBClient(url_service=url_service, creds=creds, wf_state=wf)
