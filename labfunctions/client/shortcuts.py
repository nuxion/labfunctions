import os
from typing import Optional, Union

from labfunctions import defaults, secrets, types
from labfunctions.conf import load_client
from labfunctions.utils import secure_filename

from .diskclient import DiskClient
from .labstate import LabState
from .nbclient import NBClient


def from_file(
    filepath=defaults.LABFILE_NAME, url_service=None, home_dir=defaults.CLIENT_HOME_DIR
) -> DiskClient:
    """intialize a py:class:`labfunctions.client.diskclient.DiskClient`
    using data from local like workflows.yaml.
    """

    settings = load_client()
    lab_state = LabState.from_file(filepath)
    lf_service = url_service or settings.WORKFLOW_SERVICE
    # if not creds:
    #    creds = login_cli(url_service, home_dir)
    dc = DiskClient(
        url_service=lf_service,
        lab_state=lab_state,
        base_path=settings.BASE_PATH,
    )
    dc.load_creds()
    # if not os.environ.get("DEBUG"):
    #    try:
    #        dc.logincli()
    #    except httpx.ConnectError:
    #        print("No connection with server")
    return dc


def from_env(
    settings: Optional[types.ClientSettings] = None, projectid=None
) -> NBClient:
    """Creates a client using the settings module and environment variables"""
    settings = settings or load_client()
    # nbvars = secrets.load(settings.BASE_PATH)
    # creds = _load_creds(settings, nbvars)
    pd = types.ProjectData(name=settings.PROJECT_NAME, projectid=settings.PROJECTID)
    if projectid:
        pd.projectid = projectid

    lab_state = LabState(pd)
    c = NBClient(
        url_service=settings.WORKFLOW_SERVICE,
        lab_state=lab_state,
        base_path=os.getenv(defaults.BASE_PATH_ENV),
    )
    c.load_creds()
    return c


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
    lf = LabState(types.ProjectData(name="", projectid=projectid))
    creds = types.TokenCreds(access_token=token, refresh_token=refresh)
    return NBClient(url_service=url_service, creds=creds, lab_state=lf)
