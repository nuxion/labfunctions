import os
import sys
from datetime import datetime
from pathlib import Path

import click
import httpx
from rich import print_json

# from labfunctions.io.fileserver import FileFileserver
from rich.table import Table

from labfunctions import client, defaults, errors
from labfunctions.client import init_script
from labfunctions.conf import load_client
from labfunctions.utils import format_seconds, mkdir_p

from .utils import ConfigCli, console

cliconf = ConfigCli()
URL = cliconf.data.url_service
WF = cliconf.data.lab_file


def get_notebook(nbclient, row):
    output_result = False
    if row.status == 0:
        uri = f"{row.result.output_dir}/{row.result.output_name}"
        if row.result.output_dir:
            mkdir_p(row.result.output_dir)
            output_result = True
    else:
        uri = f"{row.result.error_dir}/{row.result.output_name}"
        if row.result.output_dir:
            mkdir_p(row.result.error_dir)
            output_result = True
    if not Path(uri).exists() and output_result:
        try:
            with open(uri, "wb") as f:
                for chunk in nbclient.history_get_output(uri):
                    f.write(chunk)
        except (Exception, errors.HistoryNotebookError) as e:
            # console.print(f"[bold red]Error getting result from {uri}[/]")
            Path(uri).unlink()
            output_result = False
            console.print(f"[bold red]{e}[/]")
    return output_result, uri


@click.group(name="log")
def logcli():
    """
    History of tasks executed
    """


@logcli.command(name="list")
@click.option(
    "--from-file",
    "-f",
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the Lab Function service",
)
@click.option("--wfid", "-w", default=None, help="Execution history of workflow id")
@click.option("--last", "-l", default=1, help="The last executions")
def listcli(from_file, url_service, last, wfid):
    """List the history of tasks executions"""
    c = client.from_file(from_file, url_service=url_service)

    rsp = c.history_get_last(wfid, last)
    if not rsp:
        console.print("No history logs")
        sys.exit(0)
    table = Table(title="History")
    # table.add_column("alias", style="cyan", no_wrap=True, justify="center")
    table.add_column("wfid", style="cyan", justify="center")
    table.add_column("execid", style="cyan", justify="center")
    table.add_column("status", style="cyan", justify="center")
    table.add_column("dir_output", style="cyan", justify="center")
    table.add_column("runned", style="cyan", justify="center")

    # print("wfid | execid | status")
    for r in rsp:
        status = "[bold green]OK[/]" if r.status == 0 else "[bold red]FAIL[/]"
        pid = r.result.projectid
        dt = datetime.fromisoformat(r.created_at)
        now = datetime.utcnow()
        diff = (now - dt).total_seconds()
        run = f"[blue]{format_seconds(diff)}[/]"
        c.history_nb_output
        out, uri = get_notebook(c, r)
        if not out:
            uri = "[red bold]Output not generated[/]"

        # print(f"{r.wfid} | {r.execid} | {status} | {uri}")
        table.add_row(r.wfid, r.execid, status, uri, run)

    console.print(table)


@logcli.command(name="get")
@click.option(
    "--from-file",
    "-f",
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the Lab Function service",
)
@click.option("--nice", "-n", is_flag=True, default=True, help="Print nice output")
@click.argument("execid")
def getcli(url_service, from_file, execid, nice):
    """log detail of a execution"""
    c = client.from_file(from_file, url_service=url_service)
    rsp = c.history_detail(execid)
    if not rsp:
        console.print(f"[red bold](x) Execution id {execid} not found[/]")
        sys.exit(-1)
    if not nice:
        print_json(data=rsp.dict())
        sys.exit(0)

    console.print("=> Macro: ")
    print_json(data=rsp.dict(exclude={"result"}))
    console.print("=> Result Detail: ")
    print_json(data=rsp.result.dict(exclude={"error_msg"}))
    console.print("=> Errors: ")
    console.print(f"[red]{rsp.result.error_msg}[/]")


@logcli.command(name="task")
@click.option(
    "--from-file",
    "-f",
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the Lab Function service",
)
# @click.option("--nice", "-n", is_flag=True, default=True, help="Print nice output")
@click.argument("execid")
def taskcli(url_service, from_file, execid):
    """log detail of a execution"""
    c = client.from_file(from_file, url_service=url_service)
    rsp = c.task_status(execid)
    if not rsp:
        console.print(f"[red bold](x) Execution id {execid} not found[/]")
        sys.exit(-1)

    print_json(data=rsp.dict())
