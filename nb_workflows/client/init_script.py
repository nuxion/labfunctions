import os
import pathlib
from typing import Tuple

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from nb_workflows import client
from nb_workflows.client.diskclient import DiskClient
from nb_workflows.client.state import WorkflowsState
from nb_workflows.client.uploads import generate_dockerfile
from nb_workflows.conf import defaults, load_client
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.hashes import generate_random
from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowDataWeb
from nb_workflows.types.docker import DockerfileImage
from nb_workflows.utils import get_parent_folder

from .utils import normalize_name

console = Console()


def _example_task() -> NBTask:
    t = NBTask(
        nb_name="welcome",
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


def default_runtime() -> DockerfileImage:
    return DockerfileImage(
        maintener=defaults.DOCKERFILE_MAINTENER,
        image=defaults.DOCKERFILE_IMAGE,
        final_packages="vim-tiny",
    )


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return True


def _ask_project_name() -> str:
    parent = get_parent_folder()
    _default = normalize_name(parent)
    project_name = Prompt.ask(
        f"Write a name for this project, [yellow]please, avoid spaces and capital "
        "letters[/yellow]: ",
        default=_default,
    )
    name = normalize_name(project_name)
    console.print(
        f"The final name for the project is: [bold magenta]{name}[/bold magenta]"
    )
    return name


def init_setting_dir_app(root, projectid, project_name, url_service=None):
    # _pkg_dir = get_package_dir("nb_workflows")
    p = root / "nb_app"

    workflow_service = url_service or "http://localhost:8000"

    p.mkdir(parents=True, exist_ok=True)
    _empty_file(p / "__init__.py")
    render_to_file(
        "client_settings.py.j2",
        str((p / "settings.py").resolve()),
        data={
            "projectid": projectid,
            "project_name": project_name,
            "workflow_service": url_service,
        },
    )


def generate_cicd_files(root):

    runtime = default_runtime()
    generate_dockerfile(root, runtime.dict())

    render_to_file("Makefile", str((root / "Makefile").resolve()))
    render_to_file("dockerignore", str((root / ".dockerignore").resolve()))
    render_to_file("gitignore", str((root / ".gitignore").resolve()))


def create_dirs(base_path):
    root = pathlib.Path(base_path)
    for dir_ in ["outputs", "models", defaults.NOTEBOOKS_DIR]:
        (root / dir_).mkdir(parents=True, exist_ok=True)

    render_to_file(
        "welcome.ipynb.j2",
        str((root / defaults.NOTEBOOKS_DIR / "welcome.ipynb").resolve()),
    )


def workflow_state_init(projectid=None, name=None) -> WorkflowsState:

    wd = _example_workflow()
    wd_dict = {wd.alias: wd}
    runtime = default_runtime()

    # projectid = settings.PROJECTID
    # name = settings.PROJECT_NAME

    if not projectid:
        name = _ask_project_name()
        # rsp = httpx.get(f"{url_service}/projects/_generateid")
        # projectid = rsp.json()["projectid"]
        projectid = generate_random(defaults.PROJECTID_LEN)

    pd = ProjectData(name=name, projectid=projectid)
    wf_state = WorkflowsState(pd, workflows=wd_dict, runtime=runtime, version="0.2.0")
    wf_state.write()
    return wf_state


def create_on_the_server(dc: DiskClient):
    create = Confirm.ask("Create project in the server?", default=True)
    if create:
        dc.logincli()
        dc.projects_create()
        valid_agent = dc.projects_create_agent()
        agent_creds = dc.projects_agent_token()
        with open("local.nbvars", "w") as f:
            f.write(f"AGENT_TOKEN={agent_creds.access_token}\n")
            f.write(f"AGENT_REFRESH_TOKEN={agent_creds.refresh_token}")
    p = Panel.fit(
        "[bold magenta]:smile_cat: Congrats!!!" " Project created[/bold magenta]",
        border_style="red",
    )
    console.print(
        f"Agent for this project was created as: [bold magenta]{valid_agent}[/]"
    )
    console.print(p)


def verify_pre_existent(root) -> bool:
    # exist = (root / "local.nbvars").is_file()
    exist = False
    nb_tmp = (root / ".nb_tmp").is_dir()
    wf_file = (root / "workflows.yaml").resolve().is_file()
    if exist or nb_tmp or wf_file:
        return True
    return False


def init(root, init_dirs=True, url_service=None):
    settings = load_client()
    url = url_service or settings.WORKFLOW_SERVICE

    i_should_create = True
    if verify_pre_existent(root):
        i_should_create = Confirm.ask(
            "[yellow]It seems that a project already exist, "
            "do you want to continue?[/yellow]",
            default=False,
        )
    if i_should_create:
        _empty_file(root / "local.nbvars")
        state = workflow_state_init()
        dc = DiskClient(url_service, wf_state=state)
        create_on_the_server(dc)

        init_setting_dir_app(
            root,
            projectid=dc.projectid,
            project_name=dc.project_name,
            url_service=url_service,
        )

        generate_cicd_files(root)
        if init_dirs:
            create_dirs(root)
