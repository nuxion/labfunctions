import os

import click
from rich.console import Console

from labfunctions.cmd.common import configcli, info, login, startproject


def load_client_cli(cli):
    from labfunctions.cmd.executors import executorscli
    from labfunctions.cmd.history import logcli
    from labfunctions.cmd.project import projectcli
    from labfunctions.cmd.runtimes import runtimescli
    from labfunctions.cmd.workflows import workflowscli

    cli.add_command(workflowscli)
    cli.add_command(projectcli)
    cli.add_command(logcli)
    cli.add_command(executorscli)
    cli.add_command(runtimescli)


def load_server_cli(cli):
    from labfunctions.cmd.agent import agentcli

    # from labfunctions.cmd.cluster import clustercli
    from labfunctions.cmd.manager import managercli
    from labfunctions.cmd.runtimes import runtimescli
    from labfunctions.cmd.services import webcli

    cli.add_command(managercli)
    cli.add_command(webcli)
    cli.add_command(agentcli)
    # cli.add_command(clustercli)
    cli.add_command(runtimescli)


def init_cli():

    console = Console()

    @click.group()
    @click.pass_context
    def cli(ctx):
        """
        Lab Functions command line tool
        """

    @click.command()
    @click.pass_context
    def version(ctx):
        """Actual version"""
        from labfunctions.utils import get_version

        ver = get_version("__version__.py")
        console.print(f"[bold magenta]{ver}[/bold magenta]")

    if os.environ.get("LF_SERVER", False):
        load_server_cli(cli)

        if os.environ.get("DEBUG", False):
            # cli.add_command(executorscli)
            load_client_cli(cli)
    else:
        load_client_cli(cli)

    cli.add_command(startproject)
    cli.add_command(login)
    cli.add_command(version)
    cli.add_command(info)
    cli.add_command(configcli)
    return cli


cli = init_cli()

if __name__ == "__main__":

    cli(ctx={})
    # cli(obj={})
