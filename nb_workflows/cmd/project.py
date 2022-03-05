import click

from nb_workflows import client
from nb_workflows.uploads import zip_project


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
@click.argument("action", type=click.Choice(["upload"]))
def project(from_file, only_zip, env_file, current, action):
    """Manage project settings"""
    c = client.nb_from_file(from_file)
    if action == "upload":
        pv = client.utils.get_private_key(c.projectid)
        zfile = zip_project(pv, env_file, current)
        click.echo(f"Zipfile generated in {zfile.filepath}")
        if not only_zip:
            c.projects_upload(zfile)


projectcli.add_command(project)
