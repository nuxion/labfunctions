import os
from datetime import datetime
from pathlib import Path

import click
import httpx

# from nb_workflows.io.fileserver import FileFileserver
from rich.console import Console
from rich.table import Table

from nb_workflows import client, defaults
from nb_workflows.client import init_script
from nb_workflows.conf import load_client
from nb_workflows.utils import format_seconds, mkdir_p

console = Console()


def get_notebook(url_service, pid, row):
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
        fullurl = (
            f"{url_service}/{defaults.API_VERSION}/history/{pid}/_get_output?file={uri}"
        )
        nb = httpx.get(fullurl)
        if nb.status_code == 200:
            with open(uri, "wb") as f:
                f.write(nb.content)
        else:
            console.print(f"[bold red]Error getting result from {fullurl}[/]")
    return output_result, uri


@click.command(name="history")
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
    """Examine the history and state of your workflows"""
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
        out, uri = get_notebook(url_service, pid, r)
        if not out:
            uri = "[red bold]Output not generated[/]"

        # print(f"{r.wfid} | {r.execid} | {status} | {uri}")
        table.add_row(r.wfid, r.execid, status, uri, run)

    console.print(table)
