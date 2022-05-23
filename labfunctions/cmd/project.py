import os
import sys
from pathlib import Path

import click
from rich.table import Table

from labfunctions import client, defaults, secrets
from labfunctions.conf import load_client
from labfunctions.errors.client import ProjectUploadError
from labfunctions.utils import execute_cmd

from .utils import ConfigCli, console, watcher

cliconf = ConfigCli()
URL = cliconf.data.url_service
LF = cliconf.data.lab_file

# settings = load_client()


@click.group(name="project")
def projectcli():
    """
    Synchronize project with the server

    """


@projectcli.command()
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
@click.option(
    "--agentname",
    "-a",
    default=None,
    help="Agent Name",
)
@click.argument("action", type=click.Choice(["create", "del", "list", "token"]))
def agent(url_service, from_file, agentname, action):
    """[create, list, del, token]  of an agent"""

    c = client.from_file(from_file, url_service)

    if action == "create":
        res = c.projects_create_agent()
        if res:
            console.print("[bold green] Agent created [/]")
        else:
            console.print("[bold yellow] Agent creation fail [/]")

    elif action == "token":
        res = c.projects_agent_token(agentname)
        if res:
            console.print(f"[bold magenta]agent name:[/] {res.agent_name}")
            console.print(f"[bold magenta]access token:[/] {res.creds.access_token}")
            console.print(f"[bold magenta]refresh token:[/] {res.creds.refresh_token}")
        else:
            console.print("[bold yellow] Agent creds fail [/]")

    elif action == "list":
        res = c.projects_agent_list()
        table = Table(title="Agents")
        table.add_column("name", style="cyan", justify="center")
        for a in res:
            table.add_row(a)
        console.print(table)

    elif action == "del":
        if not agentname:
            console.print("[red bold]A agent name must be provided[/]")
            sys.exit(-1)
        res = c.project_agent_delete(agentname)
        if res:
            console.print("[bold green]Agent deleted[/]")
        else:
            console.print("[bold red]Something went wrong[/]")


@projectcli.command(name="list")
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
def listcli(url_service, from_file):
    """List projects"""
    c = client.from_file(from_file, url_service)

    projects = c.projects_list()

    table = Table(title="Projects")
    table.add_column("id", style="cyan", justify="center")
    table.add_column("name", style="cyan", justify="center")
    table.add_column("desc", style="yellow", justify="center")
    for p in projects:
        table.add_row(p.projectid, p.name, p.description)
    console.print(table)
