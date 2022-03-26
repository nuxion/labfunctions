import os

import click
from rich import print_json
from rich.console import Console

from nb_workflows import client
from nb_workflows.conf import defaults, load_client
from nb_workflows.types import NBTask

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
@click.argument("wfid")
@click.pass_context
def wf(ctx, wfid):
    """It will dispatch the workflow task to the server"""

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.from_file(from_file, url_service=url_service)
    rsp = c.workflows_enqueue(wfid)
    if rsp:
        click.echo(f"Executed: {rsp} on the server {url_service}")
    else:
        click.echo(f"Something went wrong")


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
@click.argument("notebook")
@click.pass_context
def notebook(ctx, param, machine, docker_version, dev, notebook):
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
        print_json(data=rsp.json())
    else:
        task = NBTask(
            nb_name=notebook,
            params=params_dict,
            machine=machine,
            docker_version=docker_version,
        )
        rsp = local_nb_dev_exec(task)

        print_json(data=rsp.dict())
