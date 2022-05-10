import os
import sys
from datetime import datetime
from pathlib import Path

import click
import httpx
from rich import print_json

# from labfunctions.io.fileserver import FileFileserver
from rich.console import Console
from rich.table import Table

from labfunctions import client, defaults
from labfunctions.client import init_script
from labfunctions.conf import load_client
from labfunctions.utils import format_seconds, mkdir_p

console = Console()


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
        except Exception as e:
            console.print(f"[bold red]Error getting result from {uri}[/]")
            console.print(f"[bold red]{e}[/]")
    return output_result, uri


@click.group(name="status")
def statuscli():
    """
    History of tasks executed
    """


@statuscli.command(name="history")
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=load_client().WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.option("--wfid", "-w", default=None, help="Execution history of workflow id")
@click.option("--last", "-l", default=1, help="The last executions")
def historycli(from_file, url_service, last, wfid):
    """History of tasks executions"""
    c = client.from_file(from_file, url_service=url_service)

    rsp = c.history_get_last(wfid, last)
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


@statuscli.command(name="log")
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=load_client().WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.option("--execid", "-e", default=None, help="Execution log of a task")
@click.option("--nice", "-n", is_flag=True, default=True, help="Print nice output")
def logcli(url_service, from_file, execid, nice):
    """log detail of a execution"""
    c = client.from_file(from_file, url_service=url_service)
    rsp = c.history_detail(execid)
    if not rsp:
        console.print(f"[red bold](x) Execution id {execid} not found[/]")
        sys.exit(-1)
    print_json(data=rsp.dict())
    if nice:
        console.print(f"[red]{rsp.result.error_msg}[/]")
