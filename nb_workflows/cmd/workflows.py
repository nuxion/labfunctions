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


@click.group()
def workflowscli():
    """
    wrapper
    """
    pass


@click.command()
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
def history(from_file, url_service, last, wfid):
    c = client.nb_from_file(from_file, url_service=url_service)
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


@click.command()
@click.option(
    "--from-file",
    "-f",
    default="workflows.yaml",
    help="yaml file with the configuration",
)
@click.option("--example", "-E", default=True, is_flag=True, help="Init with example")
@click.option(
    "--url-service",
    "-u",
    default=load_client().WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.option("--wfid", "-w", default=None, help="wfid to execute")
@click.option(
    "--update",
    "-u",
    is_flag=True,
    default=False,
    help="Updates workflows when push",
)
@click.option("--remote", "-r", default=False, is_flag=True, help="execute remote")
@click.argument(
    "action",
    type=click.Choice(["init", "push", "sync", "list", "exec", "dev-exec", "delete"]),
)
def wf(from_file, url_service, remote, update, example, action, wfid):
    """Manage workflows"""

    if action == "init":
        c = client.init(url_service)
        c.write()

    elif action == "push":
        c = client.nb_from_file(from_file, url_service=url_service)
        c.workflows_push(update=update)

    elif action == "list":
        c = client.nb_from_file(from_file, url_service=url_service)
        data = c.workflows_list()
        print("\nnb_name | wfid | alias | is_enabled\n")
        for d in data:
            print(f"{d.nb_name} | {d.wfid} | {d.alias} | [{d.enabled}]")

    elif action == "exec":
        c = client.nb_from_file(from_file, url_service=url_service)
        rsp = c.workflows_enqueue(wfid)
        if rsp:
            click.echo(f"Executed: {rsp} on the server {url_service}")
        else:
            click.echo(f"Something went wrong")

    elif action == "dev-exec":
        c = client.nb_from_file(from_file, url_service=url_service)
        rsp = local_dev_exec(wfid)
        if rsp:
            click.echo(f"Wfid: {rsp.wfid} locally executed")
            click.echo(f"Executionid: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")

    elif action == "delete":
        c = client.nb_from_file(from_file, url_service=url_service)
        rsp = c.workflows_delete(wfid)
        print(f"Wfid: {wfid}, deleted. Code {rsp}")

    elif action == "sync":
        c = client.nb_from_file(from_file, url_service=url_service)
        c.sync_file()
        click.echo(f"{from_file} sync")

    else:
        print("Valid actions are: [init, push, list, exec, delete]")


@click.command()
@click.option(
    "--url-service",
    "-u",
    default=load_client().WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
def login(url_service):
    """Login to NB Workflows service"""
    click.echo(f"\nLogin to NB Workflows services {url_service}\n")
    creds = client.login_cli(url_service)
    if not creds:
        click.echo(f"Error auth, try again")


@workflowscli.command()
@click.option(
    "--create-dirs",
    "-C",
    is_flag=True,
    default=True,
    help="Create outpus and workflows dir",
)
@click.argument("base_path")
def startproject(base_path, create_dirs):
    """Start a new project"""
    init_script.init(base_path, create_dirs)
    print("\n Next steps: ")
    print("\n\t1. init a git repository")
    print("\t2. create a workflow inside of the workflows folder")
    print("\t3. publish your work")
    print()


workflowscli.add_command(wf)
workflowscli.add_command(login)
workflowscli.add_command(startproject)
workflowscli.add_command(history)
