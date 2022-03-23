import os

import click
from rich.console import Console

from nb_workflows.cmd.common import login, startproject


def load_client_cli(cli):
    from nb_workflows.cmd.executors import executorscli
    from nb_workflows.cmd.history import historycli
    from nb_workflows.cmd.project import projectcli
    from nb_workflows.cmd.workflows import workflowscli

    cli.add_command(workflowscli)
    cli.add_command(projectcli)
    cli.add_command(historycli)
    cli.add_command(executorscli)


def load_server_cli(cli):
    from nb_workflows.cmd.manager import managercli
    from nb_workflows.cmd.services import rqschedulercli, rqworkercli, webcli

    cli.add_command(managercli)
    cli.add_command(webcli)
    cli.add_command(rqschedulercli)
    cli.add_command(rqworkercli)


def init_cli():

    console = Console()

    @click.group()
    @click.pass_context
    def cli(ctx):
        """
        NB Workflow command line tool
        """

    @click.command()
    @click.pass_context
    def version(ctx):
        """Actual version"""
        from nb_workflows.utils import get_version

        ver = get_version("__version__.py")
        console.print(f"[bold magenta]{ver}[/bold magenta]")

    if os.environ.get("NB_SERVER", False):
        load_server_cli(cli)

        if os.environ.get("DEBUG", False):
            # cli.add_command(executorscli)
            load_client_cli(cli)
    else:
        load_client_cli(cli)

    cli.add_command(startproject)
    cli.add_command(login)
    cli.add_command(version)
    return cli


cli = init_cli()

if __name__ == "__main__":

    cli(ctx={})
    # cli(obj={})
