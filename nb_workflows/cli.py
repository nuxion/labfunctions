import os

import click
from rich.console import Console

from nb_workflows.cmd.common import login, startproject


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
        console.print(
            f"Hello, actual version is [bold magenta]{ver}[/bold magenta]!", ":smiley:"
        )

    if os.environ.get("NB_SERVER", False):
        from nb_workflows.cmd.manager import managercli
        from nb_workflows.cmd.services import rqschedulercli, rqworkercli, webcli

        cli.add_command(managercli)
        cli.add_command(webcli)
        cli.add_command(rqschedulercli)
        cli.add_command(rqworkercli)
        # cli.add_command(executorscli)
    else:
        from nb_workflows.cmd.executors import executorscli
        from nb_workflows.cmd.history import historycli
        from nb_workflows.cmd.project import projectcli
        from nb_workflows.cmd.workflows import workflowscli

        cli.add_command(workflowscli)
        cli.add_command(projectcli)
        cli.add_command(historycli)

    cli.add_command(startproject)
    cli.add_command(login)
    cli.add_command(version)
    return cli


cli = init_cli()

if __name__ == "__main__":

    # cli()
    cli(obj={})
