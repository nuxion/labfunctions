import os
from pathlib import Path

import click

# from nb_workflows.io.fileserver import FileFileserver
import httpx
from rich.console import Console

from nb_workflows import client
from nb_workflows.client import init_script
from nb_workflows.conf import load_client
from nb_workflows.executors.development import local_dev_exec
from nb_workflows.executors.local import local_exec_env
from nb_workflows.utils import mkdir_p

service = os.getenv("NS_WORKFLOW_SERVICE", "http://localhost:8000")


@click.command()
@click.option(
    "--url-service",
    "-u",
    default=load_client().WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
def login(url_service):
    """Login to NB Workflows service"""
    click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    creds = client.login_cli(url_service)
    if not creds:
        click.echo(f"Error auth, try again")


@click.command()
@click.option(
    "--create-dirs",
    "-C",
    is_flag=True,
    default=True,
    help="Create outpus and workflows dir",
)
@click.option(
    "--url-service",
    "-u",
    default=service,
    help="URL of the NB Workflow Service",
)
@click.argument("base_path")
def startproject(url_service, create_dirs, base_path):
    """Start a new project"""

    root = Path(base_path)
    console = Console()
    console.print("=" * 80, style="magenta")
    console.print(
        f"\n Starting project at [blue underline]{root.resolve()}[/blue underline]\n"
    )
    console.print("=" * 80, style="magenta")
    console.print()

    init_script.init(
        root,
        create_dirs,
        url_service,
    )
    print("\n Next steps: ")
    print("\n\t1. init a git repository")
    print("\t2. create a workflow inside of the workflows folder")
    print("\t3. publish your work")
    print()
