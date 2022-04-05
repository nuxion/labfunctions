import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from nb_workflows import client, secrets
from nb_workflows.client.uploads import generate_dockerfile
from nb_workflows.conf import defaults, load_client
from nb_workflows.errors.client import ProjectUploadError
from nb_workflows.utils import execute_cmd

from .utils import watcher

# from nb_workflows.uploads import manage_upload

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


@projectcli.command()
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
@click.pass_context
def upload(ctx, only_zip, env_file, current, all, watch):
    """Prepare and push your porject information to the server"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    c = client.from_file(from_file, url_service)
    # prepare secrets
    pv = c.get_private_key()
    if not pv:
        print("Not private key found or authentication error")
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


@projectcli.command()
@click.pass_context
def dockerfile(ctx):
    """Render  Dockerfile.nbruntime based on nb_app/settings.py"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    root = Path(os.getcwd())
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    c = client.from_file(from_file, url_service)
    generate_dockerfile(root, c.state.runtime.dict())
    click.echo(f"{defaults.DOCKERFILE_RUNTIME_NAME} updated")
    click.echo("Remember to add this change to git...")


@projectcli.command(name="runtimes")
@click.pass_context
def runtimescli(ctx):
    """List of runtimes available for this project"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.from_file(from_file, url_service)
    runtimes = c.runtimes_get_all()
    table = Table(title="Runtimes for the project")
    # table.add_column("alias", style="cyan", no_wrap=True, justify="center")
    table.add_column("id", style="cyan", justify="center")
    table.add_column("docker_name", style="cyan", justify="center")
    table.add_column("version", style="cyan", justify="center")
    for runtime in runtimes:
        table.add_row(str(runtime.id), runtime.docker_name, runtime.version)
    console.print(table)


@projectcli.command()
@click.pass_context
def info(ctx):
    """Project's summary"""
    url_service = ctx.obj["URL"]
    c = client.from_file(url_service=url_service)
    c.info()
