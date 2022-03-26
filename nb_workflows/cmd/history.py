import os

import click

# from nb_workflows.io.fileserver import FileFileserver
import httpx

from nb_workflows import client
from nb_workflows.client import init_script
from nb_workflows.conf import load_client
from nb_workflows.executors.development import local_dev_exec
from nb_workflows.executors.local import local_exec_env
from nb_workflows.utils import mkdir_p


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
    print("wfid | execid | status")
    for r in rsp:
        status = "[OK]" if r.status == 0 else "[FAIL]"
        pid = r.result.projectid
        if r.status == 0:
            uri = f"{r.result.output_dir}/{r.result.output_name}"
            mkdir_p(r.result.output_dir)
        else:
            uri = f"{r.result.error_dir}/{r.result.output_name}"
            mkdir_p(r.result.error_dir)
        nb = httpx.get(f"http://192.168.88.150:4444/{pid}/{uri}")
        with open(uri, "wb") as f:
            f.write(nb.content)
        print(f"{r.wfid} | {r.execid} | {status} | {uri}")
