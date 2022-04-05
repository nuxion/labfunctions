import json
import os

import click
from rich import print_json
from rich.console import Console

from nb_workflows import client
from nb_workflows.client.diskclient import DiskClient
from nb_workflows.conf import defaults, load_client
from nb_workflows.executors.context import pure_execid
from nb_workflows.types import NBTask

from .utils import watcher

console = Console()


def _parse_params_args(params):
    params_dict = {}
    for p in params:
        k, v = p.split("=")
        params_dict.update({k: v})
    return params_dict


@click.group(name="exec")
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
@click.pass_context
def executorscli(ctx, url_service, from_file):
    """
    Execute workflows or notebooks, locally or remote
    """
    ctx.ensure_object(dict)

    ctx.obj["URL"] = url_service
    ctx.obj["WF_FILE"] = from_file


@executorscli.command()
@click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
@click.pass_context
def docker(ctx, wfid):
    """It will run the task inside a docker container, it exist only as a tester"""
    import json

    import docker
    from nb_workflows.executors.development import local_docker

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    local_docker(url_service, from_file, wfid)


@executorscli.command()
@click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
@click.option("--dev", "-d", default=False, is_flag=True, help="Execute locally")
@click.pass_context
def local(ctx, dev, wfid):
    """Used by the agent to run workloads or for development purposes"""

    from nb_workflows.executors.development import local_dev_exec
    from nb_workflows.executors.local import local_exec_env

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    # settings = load_client()
    if os.environ.get(defaults.EXECUTIONTASK_VAR):
        # TODO: Should be inject or validate url_service param
        # when running from the data plane machine?
        rsp = local_exec_env()
        if rsp:
            click.echo(f"WFID: {rsp.wfid} locally executed")
            click.echo(f"EXECID: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")
    elif wfid:
        c = client.from_file(from_file, url_service=url_service)
        rsp = local_dev_exec(wfid)
        if rsp:
            click.echo(f"WFID: {rsp.wfid} locally executed")
            click.echo(f"EXECID: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")

    else:
        console.print(
            f"[red]Neither [bold magenta]wfid[/bold magenta] param or "
            f"[bold magenta]{defaults.EXECUTIONTASK_VAR}[/bold magenta]"
            " were provided[/]"
        )


@executorscli.command()
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="Get events & logs from the executions",
)
@click.option(
    "--stats",
    "-s",
    is_flag=True,
    default=False,
    help="Show stats as memory usage from the execution",
)
@click.argument("wfid")
@click.pass_context
def wf(ctx, wfid, watch, stats):
    """It will dispatch the workflow task to the server"""

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.from_file(from_file, url_service=url_service)
    execid = c.workflows_enqueue(wfid)
    if execid:
        pure = pure_execid(execid)
        console.print(f"Executed: {pure} on server {url_service}")
        if watch:
            watcher(c, pure, stats=stats)
    else:
        console.print("[red]Something went wrong[/]")


@executorscli.command()
@click.option(
    "--param", "-p", multiple=True, help="Params to be passed to the notebook file"
)
@click.option(
    "--machine", "-M", default="default", help="Machine where the notebook should run"
)
@click.option(
    "--docker-version", "-D", default="latest", help="Docker image where it should run"
)
@click.option("--dev", "-d", default=False, is_flag=True, help="Execute locally")
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="Get events & logs from the executions",
)
@click.option(
    "--stats",
    "-s",
    is_flag=True,
    default=False,
    help="Show stats as memory usage from the execution",
)
@click.argument("notebook")
@click.pass_context
def notebook(ctx, param, machine, docker_version, dev, notebook, watch, stats):
    """On demand execution of a notebook file, with custom parameters"""
    from nb_workflows.executors.development import local_nb_dev_exec

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.from_file(from_file, url_service=url_service)
    params_dict = _parse_params_args(param)

    if not dev:
        rsp = c.notebook_run(
            notebook, params_dict, machine=machine, docker_version=docker_version
        )
        # print_json(rsp.json())
        if watch:
            watcher(c, rsp.execid, stats=stats)
        print_json(data=rsp.dict())
    else:
        task = NBTask(
            nb_name=notebook,
            params=params_dict,
            machine=machine,
            docker_version=docker_version,
        )
        rsp = local_nb_dev_exec(task)

        print_json(data=rsp.dict())
