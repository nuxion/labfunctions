import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from nb_workflows import client, defaults, secrets
from nb_workflows.conf import load_client
from nb_workflows.errors.client import ProjectUploadError
from nb_workflows.runtimes import generate_dockerfile
from nb_workflows.types.runtimes import RuntimeSpec
from nb_workflows.utils import execute_cmd, open_yaml

from .utils import watcher

settings = load_client()

console = Console()


@click.group(name="runtimes")
def runtimescli():
    """
    Generates and deploy runtimes

    """


@runtimescli.command()
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
@click.option(
    "--env-file",
    "-E",
    default="local.nbvars",
    help="env file to be encrypted",
)
@click.option(
    "--current",
    "-C",
    is_flag=True,
    default=False,
    help="untracked files are zipped too but the will exist in git stash",
)
@click.option(
    "--all",
    "-A",
    is_flag=True,
    default=False,
    help="It will zip all the files ignoring .gitignore =P",
)
@click.option(
    "--only-zip",
    "-z",
    is_flag=True,
    default=False,
    help="Only generates the zip file",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="Get events & logs from the executions",
)
def deploy(url_service, from_file, only_zip, env_file, current, all, watch):
    """Prepare and push your porject information to the server"""
    c = client.from_file(from_file, url_service)
    # prepare secrets
    pv = c.get_private_key()
    if not pv:
        console.print("[red bold]Not private key found or authentication error[/]")
        sys.exit(-1)

    # _agent_token = c.projects_agent_token()

    zfile = client.manage_upload(pv, env_file, current, all)
    click.echo(f"Zipfile generated in {zfile.filepath}")
    if not only_zip:
        try:
            c.projects_upload(zfile)
            console.print("[bold green]Succesfully uploaded file[/]")
            execid = c.projects_build(zfile.version)
            if not execid:
                console.print("[bold red]Error sending build task [/]")
                sys.exit(-1)

            console.print(f"Build task sent with execid: [bold magenta]{execid}[/]")
            if watch:
                watcher(c, execid, stats=False)
        except ProjectUploadError:
            console.print("[bold red]Error uploading file [/]")

    # elif action == "agent-token":
    #    creds = c.projects_agent_token()
    #    click.echo(f"access token (keep private): \n{creds.access_token}")

    # elif action == "recreate":
    #     c.projects_create()


@runtimescli.command()
@click.option(
    "--from-file",
    "-f",
    default="runtimes.yaml",
    help="yaml file with the runtime configuration",
)
@click.argument("name", default="default")
def generate(from_file, name):
    """Render  Dockerfile.[name] based on runtimes.yaml"""
    root = Path(os.getcwd())
    data = open_yaml(from_file)
    spec_data = data["runtimes"][name]
    spec = RuntimeSpec(name=name, **spec_data)

    generate_dockerfile(root, spec)
    console.print(f"[green]Dockerfile generated as Dockerfiles.{name}[/]")


# @projectcli.command(name="runtimes")
# @click.pass_context
# def runtimescli(ctx):
#     """List of runtimes available for this project"""
#     url_service = ctx.obj["URL"]
#     from_file = ctx.obj["WF_FILE"]
#     c = client.from_file(from_file, url_service)
#     runtimes = c.runtimes_get_all()
#     table = Table(title="Runtimes for the project")
#     # table.add_column("alias", style="cyan", no_wrap=True, justify="center")
#     table.add_column("id", style="cyan", justify="center")
#     table.add_column("docker_name", style="cyan", justify="center")
#     table.add_column("version", style="cyan", justify="center")
#     for runtime in runtimes:
#         table.add_row(str(runtime.id), runtime.docker_name, runtime.version)
#     console.print(table)
#
#
# @projectcli.command(name="list")
# @click.pass_context
# def listcli(ctx):
#     """List of runtimes available for this project"""
#     url_service = ctx.obj["URL"]
#     from_file = ctx.obj["WF_FILE"]
#     c = client.from_file(from_file, url_service)
#
#     projects = c.projects_list()
#
#     table = Table(title="Projects")
#     table.add_column("id", style="cyan", justify="center")
#     table.add_column("name", style="cyan", justify="center")
#     table.add_column("desc", style="yellow", justify="center")
#     for p in projects:
#         table.add_row(p.projectid, p.name, p.description)
#     console.print(table)
#
#
# @projectcli.command()
# @click.pass_context
# def info(ctx):
#     """Project's summary"""
#     url_service = ctx.obj["URL"]
#     c = client.from_file(url_service=url_service)
#     c.info()
