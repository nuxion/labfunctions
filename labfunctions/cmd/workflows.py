import os

import click

# from labfunctions.io.fileserver import FileFileserver
import httpx
from rich.console import Console
from rich.table import Table

from labfunctions import client
from labfunctions.client import init_script
from labfunctions.conf import load_client
from labfunctions.utils import mkdir_p

from .utils import ConfigCli, console

cliconf = ConfigCli()
URL = cliconf.data.url_service
LF = cliconf.data.lab_file


@click.group(name="wf")
def workflowscli():
    """
    Start the creation of new workflows in your current folder
    """


@click.command()
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--notebook",
    "-n",
    required=True,
    help="Fullpath to the notebook file",
)
@click.option(
    "--alias",
    "-a",
    required=True,
    help="An alias for this workflow",
)
def create(url_service, from_file, notebook, alias):
    """Creates a workflow definition from a Notebook,
    if the notebook file doesn't exist, it will be created.
    (Changes aren't pushed to the server until a nb wf push
    is executed)."""
    c = client.from_file(from_file, url_service=url_service)
    c.create_workflow(notebook, alias)


@workflowscli.command()
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--update",
    "-u",
    is_flag=True,
    default=False,
    help="Updates workflows when push",
)
def push(url_service, from_file, update):
    """Push workflows definitions to the server"""
    action = "updated" if update else "created"
    c = client.from_file(from_file, url_service=url_service)
    rsp = c.workflows_push(wf_file=from_file, update=update)
    for r in rsp.errors:
        console.print(f"[bold red]{r.alias} failed[/]")
    for r in rsp.created:
        console.print(f"[bold green]{r.alias} {action} with id: {r.wfid}[/]")

    if not rsp.created and not rsp.errors:
        console.print(f"[bold yellow]No changes[/]")


@workflowscli.command(name="list")
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
def list_wf(url_service, from_file):
    """List workflows registered in the server"""

    c = client.from_file(from_file, url_service=url_service)
    data = c.workflows_list()

    table = Table(title="Workflows definitions")
    table.add_column("alias", style="cyan", no_wrap=True, justify="center")
    table.add_column("wfid", style="cyan", justify="center")
    table.add_column("is_enabled", justify="right")
    for d in data:
        enabled = "[bold green]yes[/]" if d.enabled else "[bold red]no[/]"
        table.add_row(d.alias, d.wfid, enabled)

    console.print(table)


@workflowscli.command()
@click.option(
    "--from-file",
    "-f",
    default=LF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.argument("wfid", required=True)
def delete(wfid, url_service, from_file):
    """Delete a workflow definition from server"""
    c = client.from_file(from_file, url_service=url_service)
    wf = c.state.find_by_id(wfid)
    if wf:
        c.state.delete_workflow(wf.alias)
    rsp = c.workflows_delete(wfid)
    c.write()
    print(f"Wfid: {wfid}, deleted. Code {rsp}")

    # elif action == "sync":
    #     c = client.from_file(from_file, url_service=url_service)
    #     c.sync_file()
    #     click.echo(f"{from_file} sync")


workflowscli.add_command(push)
workflowscli.add_command(list_wf)
workflowscli.add_command(delete)
workflowscli.add_command(create)
# workflowscli.add_command(exec)
