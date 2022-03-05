import os
import pathlib
from typing import Tuple

from nb_workflows import client
from nb_workflows.conf import load_client
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.core.managers import projects


def _empty_file(filename):
    with open(filename, "w", encoding="utf-8") as f:
        pass


def init_client_dir_app(base_path, projectid, project_name):
    _pkg_dir = get_package_dir("nb_workflows")
    # files = pathlib.Path(f"{_pkg_dir}/conf/files")
    p = pathlib.Path(f"{base_path}/nb_app")

    p.mkdir(parents=True, exist_ok=True)
    _empty_file(p / "__init__.py")
    render_to_file(
        "client_settings.py.j2",
        str((p / "settings.py").resolve()),
        data={"projectid": projectid, "project_name": project_name},
    )


def generate_files(base_path):
    root = pathlib.Path(base_path)
    settings = load_client(settings_module="nb_app.settings")
    if settings.DOCKER_IMAGE:
        render_to_file(
            "Dockerfile",
            str((root / "Dockerfile.nbruntime").resolve()),
            data=settings.DOCKER_IMAGE,
        )

    render_to_file("Makefile", str((root / "Makefile").resolve()))
    render_to_file("dockerignore", str((root / ".dockerignore").resolve()))
    render_to_file("gitignore", str((root / ".gitignore").resolve()))


def create_dirs(base_path):
    root = pathlib.Path(base_path)
    for dir_ in ["outputs", "models", "workflows"]:
        (root / dir_).mkdir(parents=True, exist_ok=True)

    render_to_file(
        "test_workflow.ipynb.j2",
        str((root / "workflows/test_workflow.ipynb").resolve()),
    )


def workflow_init(base_path):

    # settings = load_client(settings_module="nb_app.settings")
    settings = load_client()
    nb_client = client.init(settings.WORKFLOW_SERVICE, example=True)
    # w_conf.write(str(root / "workflows.example.toml"))
    return nb_client


def init(base_path, init_dirs=True):

    root = pathlib.Path(base_path)
    print("=" * 60)
    print(f" Starting project in {root.resolve()} ")
    print("=" * 60)
    print()
    _empty_file(root / "local.nbvars")
    nb_client = workflow_init(base_path)

    init_client_dir_app(
        base_path,
        projectid=nb_client.projectid,
        project_name=nb_client.wf_file.project.name,
    )

    generate_files(base_path)
    if init_dirs:
        create_dirs(base_path)

    # workflow_init(base_path, projectid, name)
