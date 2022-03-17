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


@click.group(name="wf")
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
def workflowscli(ctx, from_file, url_service):
    """
    Start the creation of new workflows in your current folder
    """
    ctx.ensure_object(dict)

    ctx.obj["URL"] = url_service
    ctx.obj["WF_FILE"] = from_file


@workflowscli.command()
@click.pass_context
def init(ctx):
    """initialize a project"""
    url_service = ctx.obj["URL"]
    c = client.init(url_service)
    c.write()


@click.command()
@click.option(
    "--notebook",
    "-n",
    help="Fullpath to the notebook file",
)
@click.option(
    "--alias",
    "-a",
    help="An alias for this workflow",
)
@click.pass_context
def create(ctx, notebook, alias):
    """Creates a workflow definition from a Notebook,
    if the notebook file doesn't exist, it will be created.
    (Changes aren't pushed to the server until a nb wf push
    is executed)."""

    click.echo(ctx.obj["URL"])


@workflowscli.command()
@click.option(
    "--update",
    "-u",
    is_flag=True,
    default=False,
    help="Updates workflows when push",
)
@click.pass_context
def push(ctx, update):
    """Push workflows definitions to the server"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    c = client.nb_from_file(from_file, url_service=url_service)
    c.workflows_push(update=update)


@workflowscli.command(name="list")
@click.pass_context
def list_wf(ctx):
    """List workflows registered in the server"""
    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]

    c = client.nb_from_file(from_file, url_service=url_service)
    data = c.workflows_list()
    print("\nnb_name | wfid | alias | is_enabled\n")
    for d in data:
        print(f"{d.nb_name} | {d.wfid} | {d.alias} | [{d.enabled}]")


@workflowscli.command()
@click.option("--local", "-l", default=False, is_flag=True, help="execute locally")
@click.argument("wfid", required=True)
@click.pass_context
def exec(ctx, local, wfid):
    """Exec workloads remote or locally"""

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
    if not local:
        c = client.nb_from_file(from_file, url_service=url_service)
        rsp = c.workflows_enqueue(wfid)
        if rsp:
            click.echo(f"Executed: {rsp} on the server {url_service}")
        else:
            click.echo(f"Something went wrong")
    else:
        rsp = local_dev_exec(wfid)
        if rsp:
            click.echo(f"Wfid: {rsp.wfid} locally executed")
            click.echo(f"Executionid: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")


@workflowscli.command()
@click.argument("wfid", required=True)
@click.pass_context
def delete(ctx, wfid):
    """Delete a workflow definition from server"""
    c = client.nb_from_file(from_file, url_service=url_service)
    rsp = c.workflows_delete(wfid)
    print(f"Wfid: {wfid}, deleted. Code {rsp}")

    # elif action == "sync":
    #     c = client.nb_from_file(from_file, url_service=url_service)
    #     c.sync_file()
    #     click.echo(f"{from_file} sync")


workflowscli.add_command(init)
workflowscli.add_command(push)
workflowscli.add_command(list_wf)
workflowscli.add_command(exec)
workflowscli.add_command(delete)
workflowscli.add_command(create)
