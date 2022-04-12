import os
from pathlib import Path

import click

# from nb_workflows.io.fileserver import FileFileserver
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

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
    c = client.diskclient.DiskClient(url_service)
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
