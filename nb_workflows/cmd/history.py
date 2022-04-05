import os
from datetime import datetime
from pathlib import Path

import click
import httpx

# from nb_workflows.io.fileserver import FileFileserver
from rich.console import Console
from rich.table import Table

from nb_workflows import client
from nb_workflows.client import init_script
from nb_workflows.conf import load_client
from nb_workflows.executors.development import local_dev_exec
from nb_workflows.executors.local import local_exec_env
from nb_workflows.utils import format_seconds, mkdir_p

console = Console()


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
@click.option(
    "--wfid", "-w", default=None, required=True, help="Execution history of workflow id"
)
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
        run = format_seconds(diff)

        if r.status == 0:
            uri = f"{r.result.output_dir}/{r.result.output_name}"
            mkdir_p(r.result.output_dir)
        else:
            uri = f"{r.result.error_dir}/{r.result.output_name}"
            mkdir_p(r.result.error_dir)
        if not Path(uri).exists():
            nb = httpx.get(f"{url_service}/{pid}/_get_output?file={uri}")
            with open(uri, "wb") as f:
                f.write(nb.content)
        # print(f"{r.wfid} | {r.execid} | {status} | {uri}")
        table.add_row(r.wfid, r.execid, status, uri, run)

    console.print(table)
