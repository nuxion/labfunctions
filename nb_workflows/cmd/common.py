import os
from pathlib import Path

import click

# from nb_workflows.io.fileserver import FileFileserver
import httpx
from rich.console import Console
from rich.panel import Panel

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
    # click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    c = client.from_file(url_service=url_service)
    c.logincli()


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
    p = Panel.fit(
        "[bold magenta]:smile_cat: Hello and welcome to "
        " NB Workflows [/bold magenta]",
        border_style="red",
    )
    console.print(p)
    console.print(
        f"\n Starting project at [bold blue underline]{root.resolve()}[/bold blue underline]\n"
    )
    # console.print("=" * 80, style="magenta")
    console.print()

    init_script.init(
        root,
        create_dirs,
        url_service,
    )

    console.print("\n [bold underline magenta]Next steps:[/]")
    console.print("\n\t1. init a git repository")
    console.print("\t2. create a notebook inside of the notebook folder")
    console.print("\t3. generate a workflow for that notebook")
    console.print("\t4. and finally publish your work\n")

    console.print(
        " [bold magenta]To test if everything is working "
        " you can run the following command:[/]\n"
    )
    console.print("\t[bold] nb exec notebook welcome --dev -p TIMEOUT=5[/]\n")
