import os
import sys
from pathlib import Path

import click

from nb_workflows import client, secrets
from nb_workflows.client.uploads import generate_dockerfile
from nb_workflows.conf import defaults, load_client

# from nb_workflows.uploads import manage_upload

settings = load_client()


@click.group()
def projectcli():
    """
    wrapper
    """
    pass


@projectcli.command()
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
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
    "--url-service",
    "-u",
    default=settings.WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.argument(
    "action", type=click.Choice(["upload", "dockerfile", "agent-token", "recreate"])
)
def project(from_file, only_zip, env_file, current, url_service, all, action):
    """Manage project settings"""
    c = client.nb_from_file(from_file, url_service)
    if action == "upload":

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

    elif action == "dockerfile":
        root = Path(os.getcwd())
        generate_dockerfile(root, settings.DOCKER_IMAGE)
        click.echo(f"{defaults.DOCKERFILE_RUNTIME_NAME} updated")
        click.echo("Remember add this change to git...")

    elif action == "agent-token":
        creds = c.projects_agent_token()

        click.echo(f"access token (keep private): \n{creds.access_token}")

    elif action == "recreate":
        c.projects_create()


projectcli.add_command(project)
