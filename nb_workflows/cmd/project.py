import os
import sys
from pathlib import Path

import click

from nb_workflows import client, secrets
from nb_workflows.client.uploads import generate_dockerfile
from nb_workflows.conf import defaults, load_client
from nb_workflows.utils import execute_cmd

# from nb_workflows.uploads import manage_upload

settings = load_client()


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
@click.argument(
    "action", type=click.Choice(["upload", "dockerfile", "agent-token", "recreate"])
)
@click.pass_context
def upload(ctx, only_zip, env_file, current, all):
    """Prepare and push your porject information to the server"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    c = client.from_file(from_file, url_service)
    # prepare secrets
    pv = c.get_private_key()
    if not pv:
        print("Not private key found or authentication error")
        sys.exit(-1)

    _agent_token = c.projects_agent_token()

    zfile = client.manage_upload(pv, env_file, current, _agent_token, all)

    click.echo(f"Zipfile generated in {zfile.filepath}")
    if not only_zip:
        c.projects_upload(zfile)

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
    generate_dockerfile(root, settings.DOCKER_IMAGE)
    click.echo(f"{defaults.DOCKERFILE_RUNTIME_NAME} updated")
    click.echo("Remember to add this change to git...")


@projectcli.command()
@click.pass_context
def jupyter(ctx):
    """Run a jupyter instance"""
    sys.path.append(os.getcwd())
    os.environ["NS_BASE_PATH"] = os.getcwd()
    execute_cmd("jupyter lab")


@projectcli.command()
@click.pass_context
def info(ctx):
    """Project's summary"""
    url_service = ctx.obj["URL"]
    c = client.from_file(url_service=url_service)
    c.info()


projectcli.add_command(upload)
projectcli.add_command(jupyter)
