import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from labfunctions import client, defaults, runtimes
from labfunctions.client import from_file
from labfunctions.client.diskclient import DiskClient
from labfunctions.client.labstate import LabState
from labfunctions.client.nbclient import NBClient
from labfunctions.conf import load_client
from labfunctions.conf.jtemplates import get_package_dir, render_to_file
from labfunctions.hashes import generate_random
from labfunctions.types import (
    ClientSettings,
    NBTask,
    ProjectData,
    ScheduleData,
    WorkflowDataWeb,
)
from labfunctions.types.docker import DockerfileImage
from labfunctions.types.projects import ProjectCreated
from labfunctions.types.runtimes import RuntimeSpec
from labfunctions.utils import get_parent_folder, get_version, mkdir_p, normalize_name

console = Console()

DIRECTORIES = [
    "lab_app",
    "data",
    "models",
    "outputs",
    defaults.NOTEBOOKS_DIR,
]

PROJECT_FILES = [
    {"tpl": "gitignore", "dst": ".gitignore"},
    {"tpl": "dockerignore", "dst": ".dockerignore"},
    {"tpl": "welcome.ipynb.j2", "dst": "notebooks/welcome.ipynb"},
    {"tpl": "Makefile", "dst": "Makefile"},
    {"tpl": "local.nbvars.j2", "dst": "local.nbvars"},
]


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
        # schedule=ScheduleData(
        #    repeat=1,
        #    interval=10,
        # ),
    )
    return wd


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass
    return True


def ask_project_name() -> str:
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


def init_lab_app(root, projectid, project_name, url_service=None):
    # _pkg_dir = get_package_dir("labfunctions")
    p = root / "lab_app"

    workflow_service = url_service or "http://localhost:8000"

    mkdir_p(root / "lab_app")
    _empty_file(root / "lab_app" / "__init__.py")
    render_to_file(
        "client_settings.py.j2",
        str((p / "settings.py").resolve()),
        data={
            "projectid": projectid,
            "project_name": project_name,
            "workflow_service": url_service,
        },
    )


def _default_runtime(root):
    version = get_version()
    default_cpu = f"{defaults.DOCKERFILE_IMAGE}:{version}-client"
    default_gpu = (
        f"{defaults.DOCKERFILE_IMAGE}:{version}-client-cuda{defaults.DOCKER_CUDA_VER}"
    )
    render_to_file(
        "runtimes.yaml",
        str((root / f"runtimes.yaml").resolve()),
        data={"docker_cpu": default_cpu, "docker_gpu": default_gpu},
    )


def init_project_files(root, files):
    _default_runtime(root)
    for f in files:
        render_to_file(
            f["tpl"],
            str((root / f["dst"]).resolve()),
        )
    runtime = runtimes.get_spec_from_file("default")
    runtimes.generate_dockerfile(root, runtime)


def create_folders(root, folders: List[str]):
    for f in folders:
        mkdir_p(root / f)


def lab_state_init(root, name, projectid=None) -> LabState:

    wd = _example_workflow()
    wd_dict = {wd.alias: wd}
    # runtime = default_runtime()

    if not projectid:
        projectid = generate_random(
            defaults.PROJECTID_MIN_LEN, alphabet=defaults.PROJECT_ID_ALPHABET
        )

    pd = ProjectData(name=name, projectid=projectid)
    lab_state = LabState(pd, workflows=wd_dict)
    lab_state.write(root / defaults.LABFILE_NAME)
    return lab_state


def create_on_the_server(
    root, dc: DiskClient, state: LabState
) -> Union[ProjectCreated, None]:
    rsp = dc.projects_create(
        state.project_name,
        desc=state.project.description,
        repository=state.project.repository,
        store_key=True,
    )
    if rsp:
        dc.state.projectid = rsp.pd.projectid

        return rsp
    return None


def verify_pre_existent(root) -> bool:
    # exist = (root / "local.nbvars").is_file()
    lab_file = (root / defaults.LABFILE_NAME).resolve().is_file()
    if lab_file:
        return True
    return False


def final_words(project_name, agent_name=None):
    p = Panel.fit(
        "[bold magenta]:smile_cat: Congrats!!!"
        f" Project [cyan]{project_name}[/cyan] created[/bold magenta]",
        border_style="red",
    )
    if agent_name:
        console.print(
            f"Agent for this project was created as: [bold magenta]{agent_name}[/]"
        )
    console.print(p)

    console.print("\n [bold underline magenta]Next steps:[/]")
    console.print("\n\t1. init a git repository")
    console.print("\t2. create a notebook inside of the notebook folder")
    console.print("\t3. generate a workflow for that notebook")
    console.print("\t4. and finally publish your work\n")

    console.print(
        " [bold magenta]To test if everything is working "
        " you can run the following command:[/]\n"
    )
    console.print("\t[bold] lab exec notebook welcome --local -p TIMEOUT=5[/]\n")


def i_should_create(root):
    ask = True
    if verify_pre_existent(root):
        ask = Confirm.ask(
            "[yellow]It seems that a project already exist, "
            "do you want to continue?[/yellow]",
            default=False,
        )
    return ask


def init_automatic(
    base_path: str,
    project_name: str,
    url_service: str,
    settings: Optional[ClientSettings] = None,
) -> LabState:
    root = Path(base_path)
    settings = settings or load_client()

    create_folders(root, DIRECTORIES)
    init_project_files(root, PROJECT_FILES)

    state = lab_state_init(root, project_name)
    init_lab_app(root, state.projectid, project_name, url_service)
    return state


def refresh_project(root, pc: ProjectCreated, url_service: str):
    state = lab_state_init(root, pc.pd.name, pc.pd.projectid)
    init_lab_app(root, state.projectid, pc.pd.name, url_service)
