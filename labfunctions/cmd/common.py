import os
from pathlib import Path

import click

# from labfunctions.io.fileserver import FileFileserver
import httpx
from httpx import ConnectError
from rich import print_json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from labfunctions import client
from labfunctions.client import init_script
from labfunctions.conf import load_client
from labfunctions.utils import mkdir_p

service = os.getenv("NS_WORKFLOW_SERVICE", "http://localhost:8000")
console = Console()


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
    c = client.diskclient.DiskClient(url_service)
    try:
        c.logincli()
        console.print("[bold green]Successfully logged")
    except ConnectError:
        console.print(
            f"[bold red]Error trying to connect to [magenta]{url_service}[/magenta][/]"
        )


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

    should_create = True
    if init_script.i_should_create(root):
        console.print(
            f"\n Starting project at [bold blue underline]{root.resolve()}[/bold blue underline]\n"
        )

        created = False
        confirm = True
        while not created and confirm:
            name = init_script.ask_project_name()
            state = init_script.init_automatic(base_path, name, url_service)
            create = Confirm.ask("Create project in the server?", default=True)
            if create:
                dc = client.diskclient.DiskClient(url_service, wf_state=state)
                dc.logincli()
                created = init_script.create_on_the_server(root, dc, state)
                if created:
                    init_script.final_words(created.pd.name)
                    init_script.refresh_project(root, created, url_service)
                else:
                    confirm = Confirm.ask(
                        "Do you want to try another name for the project?", default=True
                    )
            else:
                created = True
                init_script.final_words(state.project_name)


@click.command()
@click.option(
    "--url-service",
    "-u",
    default=None,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
)
def info(url_service, from_file):
    """General info and status of the client"""
    # click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    if Path(from_file).is_file():
        c = client.from_file()
    else:
        settings = load_client()
        url_service = settings.WORKFLOW_SERVICE
        c = client.from_env(settings)

    print_json(data=c.info())
