import os
import pathlib
from typing import Tuple

import httpx
from rich.console import Console
from rich.prompt import Confirm, Prompt

from nb_workflows import client
from nb_workflows.client.diskclient import DiskClient
from nb_workflows.client.state import WorkflowsState
from nb_workflows.client.uploads import generate_dockerfile
from nb_workflows.conf import defaults, load_client
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowDataWeb
from nb_workflows.utils import get_parent_folder

from .utils import login_cli, normalize_name

console = Console()


def _example_task() -> NBTask:
    t = NBTask(
        nb_name="test_workflow",
        description="An example of how to configure a specific workflow",
        params=dict(TIMEOUT=5),
    )
    return t


def _example_workflow() -> WorkflowDataWeb:
    wd = WorkflowDataWeb(
        alias="a_workflow_example",
        nbtask=_example_task(),
        enabled=False,
        schedule=ScheduleData(
            repeat=1,
            interval=10,
        ),
    )
    return wd


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return True


def _ask_project_name() -> str:
    parent = get_parent_folder()
    _default = normalize_name(parent)
    project_name = Prompt.ask(
        f"Write a name for this project, [red]please, avoid spaces and capital "
        "letters[/red]: ",
        default=_default,
    )
    name = normalize_name(project_name)
    console.print("The final name for the project is: ", name)
    return name


def init_client_dir_app(root, projectid, project_name):
    _pkg_dir = get_package_dir("nb_workflows")
    p = root / "nb_app"

    p.mkdir(parents=True, exist_ok=True)
    _empty_file(p / "__init__.py")
    render_to_file(
        "client_settings.py.j2",
        str((p / "settings.py").resolve()),
        data={"projectid": projectid, "project_name": project_name},
    )


def generate_files(root):
    settings = load_client(settings_module="nb_app.settings")
    if settings.DOCKER_IMAGE:
        generate_dockerfile(root, settings.DOCKER_IMAGE)

    render_to_file("Makefile", str((root / "Makefile").resolve()))
    render_to_file("dockerignore", str((root / ".dockerignore").resolve()))
    render_to_file("gitignore", str((root / ".gitignore").resolve()))


def create_dirs(base_path):
    root = pathlib.Path(base_path)
    for dir_ in ["outputs", "models", defaults.NOTEBOOKS_DIR]:
        (root / dir_).mkdir(parents=True, exist_ok=True)

    render_to_file(
        "test_workflow.ipynb.j2",
        str((root / defaults.NOTEBOOKS_DIR / "test_workflow.ipynb").resolve()),
    )


def client_workflow_init(url_service):
    settings = load_client()
    url = url_service or settings.WORKFLOW_SERVICE

    wd = _example_workflow()
    wd_dict = {wd.alias: wd}

    creds = login_cli(url)

    projectid = settings.PROJECTID
    name = settings.PROJECT_NAME

    if not projectid:
        name = _ask_project_name()
        rsp = httpx.get(f"{url_service}/projects/_generateid")
        projectid = rsp.json()["projectid"]

    pd = ProjectData(name=name, projectid=projectid)
    wf_state = WorkflowsState(pd, workflows=wd_dict, version="0.2.0")

    _client = DiskClient(
        url_service,
        projectid=projectid,
        creds=creds,
        wf_state=wf_state,
        version="0.2.0",
    )

    _client.write()
    # w_conf.write(str(root / "workflows.example.toml"))
    return _client


def create_on_the_server(nbclient: DiskClient):
    create = Confirm.ask("Create project in the server?", default=True)
    if create:
        nbclient.projects_create()


def verify_pre_existent(root) -> bool:
    # exist = (root / "local.nbvars").is_file()
    exist = False
    nb_tmp = (root / ".nb_tmp").is_dir()
    wf_file = (root / "workflows.yaml").resolve().is_file()
    if exist or nb_tmp or wf_file:
        return True
    return False


def init(root, init_dirs=True, url_service=None):

    create = True
    if verify_pre_existent(root):
        create = Confirm.ask(
            "It seems that a project already exist, do you want to continue?",
            default=False,
        )
    if create:
        _empty_file(root / "local.nbvars")
        nb_client = client_workflow_init(url_service)
        create_on_the_server(nb_client)

        init_client_dir_app(
            root,
            projectid=nb_client.projectid,
            project_name=nb_client.state.project.name,
        )

        generate_files(root)
        if init_dirs:
            create_dirs(root)

    # workflow_init(base_path, projectid, name)
