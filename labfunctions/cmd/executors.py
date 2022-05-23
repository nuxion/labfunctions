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

from .utils import ConfigCli, console, watcher

cliconf = ConfigCli()
URL = cliconf.data.url_service
WF = cliconf.data.lab_file


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
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the Lab Function service",
)
@click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
@click.option("--local", "-L", default=False, is_flag=True, help="Execute locally")
def local(from_file, url_service, local, wfid):
    """Used by the agent to run workloads or for development purposes"""
    rsp = None

    if os.environ.get(defaults.EXECUTIONTASK_VAR):

        nbclient = client.from_env()
        console.print(f"=> Starting work inside container")
        console.print(f"=> Current dir: {os.getcwd()}")
        console.print(f"=> Base PATH: {nbclient.base_path}")
        console.print(f"=> Service url: {nbclient._addr}")
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


# @executorscli.command()
# @click.option(
#     "--from-file",
#     "-f",
#     default=WF,
#     help="yaml file with the configuration",
# )
# @click.option(
#     "--url-service",
#     "-u",
#     default=URL,
#     help="URL of the NB Workflow Service",
# )
# @click.option("--wfid", "-W", default=None, help="Workflow ID to execute")
# @click.option("--notebook", "-n", default=None, help="Notebook to execute")
# @click.argument("action", type=click.Choice(["workflow", "notebook"]))
# def docker(from_file, url_service, notebook, wfid, action):
#     """It will run the task inside a docker container, it exist only as a tester"""
#     if wfid and not notebook:
#         c = client.from_file(from_file, url_service=url_service)
#         exec_task = c.build_context(wfid)
#         os.environ["LF_AGENT_TOKEN"] = c.creds.access_token
#         os.environ["LF_AGENT_REFRESH_TOKEN"] = c.creds.refresh_token
#         os.environ["LF_WORKFLOW_SERVICE"] = url_service
#         result = docker_exec(exec_task)
#         print_json(data=result.dict())


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
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--param",
    "-p",
    multiple=True,
    help="Params to be passed to the notebook file",
)
@click.option(
    "--machine",
    "-m",
    default="cpu",
    help="Machine where the notebook should run",
)
@click.option("--runtime", "-r", default=None, help="Runtime to use")
@click.option("--cluster", "-c", default="default", help="Cluster where it should run")
@click.option("--version", "-v", default=None, help="Runtime version to run")
@click.option("--local", "-L", default=False, is_flag=True, help="Execute locally")
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
    local,
    notebook,
    watch,
):
    """On demand execution of a notebook file, with custom parameters"""
    # from labfunctions.executors.development import local_nb_dev_exec

    c = client.from_file(from_file, url_service=url_service)
    params_dict = _parse_params_args(param)

    if not local:
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
        os.environ["LF_LOCAL"] = "yes"
        result = local_exec_env()
        # rsp = local_nb_dev_exec(task)
        print_json(data=result.dict())


@executorscli.command()
# @click.option("--runtime", "-r", default=None, help="Runtime to use")
# @click.option("--version", "-v", default=None, help="Runtime version to run")
@click.option("--addr", "-a", default="127.0.0.1", help="Address to listen")
@click.option("--image", "-i", default=None, help="Docker image to use")
@click.option("--local", "-L", default=False, is_flag=True, help="Run local")
@click.option(
    "--docker", "-D", default=False, is_flag=True, help="Execute inside docker"
)
@click.option("--remote", "-R", default=False, is_flag=True, help="Run remote")
def jupyter(
    image,
    addr,
    docker,
    local,
    remote,
):
    """Jupyter instance on demand"""
    import os

    if local and not docker:
        # user local
        ctx = jupyter_exec.create_jupyter_ctx(addr)
        ctx.set_env()
        jupyter_exec.jupyter_exec(install_jupyter=False)
    elif local and docker:
        # usar local but inside docker
        ctx = jupyter_exec.create_jupyter_ctx(addr)
        res = jupyter_exec.jupyter_docker_exec(addr, image)
        console.print(res.msg)
    elif remote:
        # post a request to create a remote jupyter instance
        console.print("[bold yellow]Not implemented to run remote[/]")
        console.print("[bold yellow]Use -L instead[/]")
    elif not local and docker:
        # used by the control plane to start a jupyter instance
        # ctx = jupyter_exec.create_jupyter_ctx(addr)
        result = jupyter_exec.jupyter_exec(install_jupyter=True)
        if result.error:
            console.print(f"[bold red]{result.messages}[/]")
    else:
        console.print("[bold red]Bad use of parameters[/]")
        sys.exit(-1)
