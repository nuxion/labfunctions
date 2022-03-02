import pathlib

from nb_workflows import client
from nb_workflows.conf import load_client
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file


def init_client_app(base_path):
    _pkg_dir = get_package_dir('nb_workflows')
    # files = pathlib.Path(f"{_pkg_dir}/conf/files")
    p = pathlib.Path(f"{base_path}/nb_app")

    p.mkdir(parents=True, exist_ok=True)
    with open(p / "__init__.py", "w") as f:
        pass
    render_to_file("client_settings.py.j2", str((p / "settings.py").resolve()))


def generate_files(base_path):
    root = pathlib.Path(base_path)
    settings = load_client(settings_module="nb_app.settings")
    if settings.DOCKER_OPTIONS:
        render_to_file("Dockerfile", str((root / "Dockerfile.nbruntime")
                                         .resolve()),
                       data=settings.DOCKER_OPTIONS)

    render_to_file("Makefile", str((root / "Makefile").resolve()))
    render_to_file("dockerignore", str((root / ".dockerignore").resolve()))
    render_to_file("gitignore", str((root / ".gitignore").resolve()))


def create_dirs(base_path):
    root = pathlib.Path(base_path)
    for dir_ in ["outputs", "models", "workflows"]:
        (root / dir_).mkdir(parents=True, exist_ok=True)

    render_to_file("test_workflow.ipynb.j2", str(
        (root / "workflows/test_workflow.ipynb").resolve()))


def workflow_init(base_path):
    root = pathlib.Path(base_path)

    settings = load_client(settings_module="nb_app.settings")
    w_conf = client.init(settings.WORKFLOW_SERVICE, example=True)
    w_conf.write(str(root / "workflows.example.toml"))


def init(base_path, init_dirs=True):

    root = pathlib.Path(base_path)
    print("="*60)
    print(f" Starting project in {root.resolve()} ")
    print("="*60)
    print()
    init_client_app(base_path)

    generate_files(base_path)
    if init_dirs:
        create_dirs(base_path)

    workflow_init(base_path)
