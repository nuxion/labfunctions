import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from nb_workflows import client, defaults, secrets
from nb_workflows.conf import load_client
from nb_workflows.errors.client import ProjectUploadError
from nb_workflows.utils import execute_cmd

from .utils import watcher

settings = load_client()

console = Console()


@click.group(name="project")
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=settings.WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.pass_context
def projectcli(ctx, url_service, from_file):
    """
    Synchronize project with the server

    """
    ctx.ensure_object(dict)

    ctx.obj["URL"] = url_service
    ctx.obj["WF_FILE"] = from_file


@projectcli.command()
@click.argument("action", type=click.Choice(["create", "token"]))
@click.pass_context
def agent(ctx, action):
    """Create/delete or get credentials of an agent"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    c = client.from_file(from_file, url_service)

    if action == "create":
        res = c.projects_create_agent()
        if res:
            console.print("[bold green] Agent created [/]")
        else:
            console.print("[bold yellow] Agent creation fail [/]")

    elif action == "token":
        res = c.projects_agent_token()
        if res:
            console.print(f"[bold magenta]access token:[/] {res.access_token}")
            console.print(f"[bold magenta]refresh token:[/] {res.refresh_token}")
        else:
            console.print("[bold yellow] Agent creds fail [/]")


@projectcli.command(name="list")
@click.pass_context
def listcli(ctx):
    """List projects"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.from_file(from_file, url_service)

    projects = c.projects_list()

    table = Table(title="Projects")
    table.add_column("id", style="cyan", justify="center")
    table.add_column("name", style="cyan", justify="center")
    table.add_column("desc", style="yellow", justify="center")
    for p in projects:
        table.add_row(p.projectid, p.name, p.description)
    console.print(table)


@projectcli.command()
@click.pass_context
def info(ctx):
    """Project's summary"""
    url_service = ctx.obj["URL"]
    c = client.from_file(url_service=url_service)
    c.info()
