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
from .utils import _example_task, get_credentials_disk, validate_credentials_local


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
    # creds = get_credentials_disk(home_dir)
    # if not creds:
    #    creds = login_cli(url_service, home_dir)
    dc = DiskClient(
        url_service=settings.WORKFLOW_SERVICE,
        wf_state=wf_state,
    )
    dc.logincli()
    return dc


def from_env(settings=load_client()) -> NBClient:
    """Creates a client using env variables"""
    tasks = None
    creds = Credentials(
        access_token=settings.AGENT_TOKEN,
        refresh_token=settings.AGENT_REFRESH_TOKEN,
    )
    pd = ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID)

    wf_state = WorkflowsState(pd)
    return NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        creds=creds,
        wf_state=wf_state,
    )


def minimal_client(url_service, token, refresh, projectid) -> NBClient:
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
    )


def agent(url_service, token, refresh, projectid) -> NBClient:
    """A shortcut to intialize :class:`nb_workflows.client.agent_client.AgentClient`

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


# def create_ctx(wfid=None) -> ExecutionNBTask:
#     ctx_str = os.getenv(defaults.EXECUTIONTASK_VAR)
#     if ctx_str:
#         exec_ctx = ExecutionNBTask(**json.loads(ctx_str))
#     else:
#         execid = context.ExecID()
#         wf = NBClient.read("workflows.yaml")
#         pd = wf.project
#         pd.username = "dummy"
#         wf_data = None
#         if wfid:
#             for w in wf.workflows:
#                 if w.wfid == wfid:
#                     wf_data = w
#         else:
#             # TODO: dumy nb_name
#             wf_data = NBTask(nb_name="test", params={})
#
#         exec_ctx = context.create_notebook_ctx(pd, wf_data, execid.pure())
#     return exec_ctx
