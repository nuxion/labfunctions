import os
import sys
from pathlib import Path

import click

# from labfunctions.io.fileserver import FileFileserver
import httpx
from httpx import ConnectError
from rich import print_json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from labfunctions import client, defaults
from labfunctions.client import init_script
from labfunctions.conf import load_client
from labfunctions.utils import mkdir_p

from .utils import ConfigCli

cliconf = ConfigCli()
service = cliconf.data.url_service
labfile = cliconf.data.lab_file
console = Console()


@click.command()
@click.option(
    "--url-service",
    "-u",
    default=service,
    help="URL of the Lab Functions",
)
@click.option(
    "--relogin",
    "-r",
    is_flag=True,
    default=False,
    help="Renew login",
)
def login(url_service, relogin):
    """Login to NB Workflows service"""
    # click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    c = client.diskclient.DiskClient(url_service)
    if relogin:
        Path(f"{c.homedir}/{defaults.CLIENT_CREDS_FILE}").unlink()
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

    root = Path(base_path).resolve()
    console = Console()
    p = Panel.fit(
        "[bold magenta]:smile_cat: Hello and welcome to "
        " LabFunctions [/bold magenta]",
        border_style="red",
    )
    console.print(p)

    should_create = True
    if init_script.i_should_create(root):
        console.print(
            f"\n Starting project at [bold blue underline]{root}[/bold blue underline]\n"
        )

        created = False
        confirm = True
        while not created and confirm:
            name = init_script.ask_project_name()
            state = init_script.init_automatic(base_path, name, url_service)
            create = Confirm.ask("Create project in the server?", default=True)
            if create:
                dc = client.diskclient.DiskClient(url_service, lab_state=state)
                dc.create_homedir()
                try:
                    dc.logincli()
                    created = init_script.create_on_the_server(root, dc, state)
                except httpx.ConnectError:
                    console.print(f"[red bold]Error connecting to {url_service}[/]")
                    sys.exit(-1)
                if created:
                    init_script.final_words(created.pd.name)
                    init_script.refresh_project(root, created, url_service)
                else:
                    confirm = Confirm.ask(
                        "Do you want to try another name for the project?",
                        default=True,
                    )
            else:
                created = True
                init_script.final_words(state.project_name)


@click.command()
@click.option(
    "--url-service",
    "-u",
    default=service,
    help="URL of the LabFunctions Service",
)
@click.option(
    "--from-file",
    "-f",
    default=labfile,
    help="yaml file with the configuration",
)
def info(url_service, from_file):
    """General info and status of the client"""
    # click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    import os

    current = ""
    if Path(from_file).is_file():
        c = client.from_file()
    else:
        settings = load_client()
        url_service = settings.WORKFLOW_SERVICE
        c = client.from_env(settings)

    print_json(data=c.info())


@click.group("config")
def configcli():
    """Manage basic configs for Lab Functions"""


@configcli.command("set")
@click.argument("key")
@click.argument("value")
def setcli(key, value):
    cliconf.set(key, value)
    console.print(f"Key {key} set")


@configcli.command("get")
@click.argument("key")
def getcli(key):
    value = cliconf.get(key)
    console.print(f"Key {key}: {value}")


@configcli.command("list")
def listcli():
    keys = cliconf.list()
    for k in keys:
        v = cliconf.get(k)
        console.print(f"{k}: {v}")
