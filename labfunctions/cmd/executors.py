import json
import os
import sys

import click
from rich import print_json

from labfunctions import client, defaults
from labfunctions.client.diskclient import DiskClient
from labfunctions.conf import load_client
from labfunctions.context import create_dummy_ctx
from labfunctions.executors import jupyter_exec
from labfunctions.executors.docker_exec import docker_exec
from labfunctions.executors.local_exec import local_exec_env
from labfunctions.hashes import generate_random
from labfunctions.types import NBTask

from .utils import console, watcher


def _parse_params_args(params):
    params_dict = {}
    for p in params:
        k, v = p.split("=")
        params_dict.update({k: v})
    return params_dict


@click.group(name="exec")
def executorscli():
    """
    Execute workflows or notebooks, locally or remote
    """


@executorscli.command()
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
@click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
@click.option("--dev", "-d", default=False, is_flag=True, help="Execute locally")
def local(from_file, url_service, dev, wfid):
    """Used by the agent to run workloads or for development purposes"""
    rsp = None

    if os.environ.get(defaults.EXECUTIONTASK_VAR):
        console.print(f"=> Starting work")
        rsp = local_exec_env()

    elif wfid:
        c = client.from_file(from_file, url_service=url_service)
        exec_task = c.build_context(wfid)
        os.environ[defaults.EXECUTIONTASK_VAR] = exec_task.json()
        rsp = local_exec_env()
    else:
        console.print(
            f"[red]Neither [bold magenta]wfid[/bold magenta] param or "
            f"[bold magenta]{defaults.EXECUTIONTASK_VAR}[/bold magenta]"
            " was provided[/]"
        )
        sys.exit(-1)

    if rsp:
        status = "OK"
        if rsp.error:
            console.print(f"[bold red](X) WFID: {rsp.wfid} failed[/]")
            sys.exit(-1)
        console.print(f"=>[bold green] WFID: {rsp.wfid} locally executed[/]")


@executorscli.command()
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
@click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
@click.option("--notebook", "-n", default=None, help="Notebook to execute")
@click.argument("action", type=click.Choice(["workflow", "notebook"]))
def docker(from_file, url_service, notebook, wfid, action):
    """It will run the task inside a docker container, it exist only as a tester"""
    if wfid and not notebook:
        c = client.from_file(from_file, url_service=url_service)
        exec_task = c.build_context(wfid)
        os.environ["NB_AGENT_TOKEN"] = c.creds.access_token
        os.environ["NB_AGENT_REFRESH_TOKEN"] = c.creds.refresh_token
        os.environ["NB_WORKFLOW_SERVICE"] = url_service
        result = docker_exec(exec_task)
        print_json(data=result.dict())


# @executorscli.command()
# @click.option(
#    "--watch",
#    "-w",
#    is_flag=True,
#    default=False,
#    help="Get events & logs from the executions",
# )
# @click.option(
#    "--stats",
#    "-s",
#    is_flag=True,
#    default=False,
#    help="Show stats as memory usage from the execution",
# )
# @click.argument("wfid")
# @click.pass_context
# def wf(ctx, wfid, watch, stats):
#    """It will dispatch the workflow task to the server"""
#
#    url_service = ctx.obj["URL"]
#    from_file = ctx.obj["WF_FILE"]
#    c = client.from_file(from_file, url_service=url_service)
#    execid = c.workflows_enqueue(wfid)
#    # if execid:
#    console.print(f"Executed: {execid} on server {url_service}")
#    if watch:
#        watcher(c, execid, stats=stats)
#    else:
#        console.print("[red]Something went wrong[/]")
#
#
@executorscli.command()
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
    "--param", "-p", multiple=True, help="Params to be passed to the notebook file"
)
@click.option(
    "--machine", "-m", default="cpu", help="Machine where the notebook should run"
)
@click.option("--runtime", "-r", default=None, help="Runtime to use")
@click.option("--cluster", "-c", default="default", help="Cluster where it should run")
@click.option("--version", "-v", default=None, help="Runtime version to run")
@click.option("--dev", "-d", default=False, is_flag=True, help="Execute locally")
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="Get events & logs from the executions",
)
@click.argument("notebook")
def notebook(
    url_service,
    from_file,
    param,
    cluster,
    runtime,
    machine,
    version,
    dev,
    notebook,
    watch,
):
    """On demand execution of a notebook file, with custom parameters"""
    # from labfunctions.executors.development import local_nb_dev_exec

    c = client.from_file(from_file, url_service=url_service)
    params_dict = _parse_params_args(param)

    if not dev:
        rsp = c.notebook_run(
            notebook,
            params_dict,
            cluster=cluster,
            machine=machine,
            runtime=runtime,
            version=version,
        )
        # print_json(rsp.json())
        if watch:
            watcher(c, rsp.execid, stats=False)
        print_json(data=rsp.dict())
    else:
        ctx = create_dummy_ctx(c.projectid, notebook, params_dict)
        os.environ[defaults.EXECUTIONTASK_VAR] = ctx.json()
        result = local_exec_env()
        # rsp = local_nb_dev_exec(task)
        print_json(data=result.dict())


@executorscli.command()
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
    "--param", "-p", multiple=True, help="Params to be passed to the notebook file"
)
@click.option(
    "--machine", "-m", default="cpu", help="Machine where the notebook should run"
)
@click.option("--runtime", "-r", default=None, help="Runtime to use")
@click.option("--cluster", "-c", default="default", help="Cluster where it should run")
@click.option("--version", "-v", default=None, help="Runtime version to run")
@click.option("--local", "-L", default=False, is_flag=True, help="Execute locally")
def jupyter(
    url_service,
    from_file,
    param,
    cluster,
    runtime,
    machine,
    version,
    local,
):
    """Jupyter instance on demand"""

    c = client.from_file(from_file, url_service=url_service)
    if local:
        os.environ["NB_LOCAL"] = "yes"
        random_url = generate_random(alphabet=defaults.NANO_URLSAFE_ALPHABET)
        opts = jupyter_exec.JupyterOpts(base_url=f"/{random_url}")
        jupyter_exec.jupyter_exec(opts)
