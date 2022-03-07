import os
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
    help="untracked files are zipped too",
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
@click.argument("action", type=click.Choice(["upload", "dockerfile"]))
def project(from_file, only_zip, env_file, current, url_service, action):
    """Manage project settings"""
    c = client.nb_from_file(from_file, url_service)
    if action == "upload":

        # prepare secrets
        pv = client.utils.get_private_key(c.projectid)
        _agent_token = c.projects_agent_token()

        zfile = client.manage_upload(pv, env_file, current, _agent_token)

        click.echo(f"Zipfile generated in {zfile.filepath}")
        if not only_zip:
            c.projects_upload(zfile)

    elif action == "dockerfile":
        root = Path(os.getcwd())
        generate_dockerfile(root, settings.DOCKER_IMAGE)
        click.echo(f"{defaults.DOCKERFILE_RUNTIME_NAME} updated")
        click.echo("Remember add this change to git...")


projectcli.add_command(project)