import os

import click
from nb_workflows import client, init_script
from nb_workflows.conf import settings_client as settings
from nb_workflows.workflows.dispatchers import local_exec


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
    default="workflows.toml",
    help="toml file with the configuration",
)
@click.option("--example", "-E", default=True, is_flag=True,
              help="Init with example")
@click.option("--url-service", "-u",
              default=settings.WORKFLOW_SERVICE, help="URL of the NB Workflow Service")
@click.option("--jobid", "-J", default=None, help="Jobid to execute")
@click.option(
    "--update",
    "-u",
    is_flag=True,
    default=False,
    help="Updates workflows when push",
)
@click.option(
    "--remote", "-r", default=False, is_flag=True, help="execute remote"
)
@click.argument(
    "action",
    type=click.Choice(["init", "push", "list", "exec", "delete", "login"]),
)
def wf(from_file, url_service, remote, update, example, action, jobid):
    """Manage workflows"""

    if action == "init":
        c = client.init(url_service)
        c.write()

    elif action == "push":
        c = client.from_file(from_file)
        c.push_workflows(update=update)

    elif action == "list":
        c = client.from_file(from_file)
        data = c.list_scheduled()
        print("\nnb_name | jobid | description | is_enabled\n")
        for d in data:
            print(f"{d.nb_name} | {d.jobid} | {d.description} | [{d.enabled}]")

    elif action == "exec":
        c = client.from_file(from_file)
        if remote:
            rsp = c.execute_remote(jobid)
            if rsp.status_code == 202:
                print(f"Jobid: {jobid}, scheduled.")
                print(f"Executionid: {rsp.executionid}")
        else:
            # creds = client.get_credentials()
            # if not os.environ.get("NB_CLIENT_TOKEN"):
            #    os.environ["NB_CLIENT_TOKEN"] = creds.access_token
            #    os.environ["NB_CLIENT_REFRESH"] = creds.refresh_token
            rsp = local_exec(jobid)
            if rsp:
                click.echo(f"Jobid: {rsp.jobid} locally executed")
                click.echo(f"Executionid: {rsp.executionid}")
                click.echo(f"Status: {rsp.error}")

    elif action == "delete":
        c = client.from_file(from_file)
        rsp = c.delete(jobid)
        print(f"Jobid: {jobid}, deleted. Code {rsp}")

    elif action == "login":
        click.echo(f"\nLogin to NB Workflows services {url_service}\n")
        creds = client.login_cli(url_service)
        if not creds:
            click.echo(f"Error auth, try again")
            # click.echo(f"ACCESS TOKEN: {token}")

    else:
        print("Valid actions are: [init, push, list, exec, delete]")


@click.command()
@click.option(
    "--from-file",
    "-f",
    default="workflows.toml",
    help="toml file with the configuration",
)
@click.argument("jobid")
def history(from_file, jobid):
    """Get the last exectuion of a workflow from the history"""

    c = client.from_file(from_file)
    r = c.history_last(jobid)
    print("Notebook: ", r["result"]["name"])
    print("Execution ID: ", r["executionid"])
    print("Status: ", r["status"])
    print("Elapsed: ", r["result"]["elapsed_secs"])
    print("Last Run: ", r["created_at"])


# @click.command()
# @click.option(
#    "--from-file",
#    "-f",
#    default="workflows.toml",
#    help="toml file with the configuration",
# )
# @click.option("--jobid", "-J", help="Jobid to operate with")
# @click.argument("action", type=click.Choice(["status"]))
# def rq(from_file, jobid, action):
#    """Information of running jobs"""
#    token = _get_token(from_file)
#    c = client.from_file(from_file, token)
#    if action == "status":
#        s = c.rq_status(jobid)
#        click.echo(s)


@workflowscli.command()
@click.option("--create-dirs", "-C", is_flag=True, default=True,
              help="Create outpus and workflows dir")
@click.argument("base_path")
def startproject(base_path, create_dirs):
    """Start a new project """
    init_script.init(base_path, create_dirs)
    print("\n Next steps: ")
    print("\n\t1. init a git repository")
    print("\t2. create a workflow inside of the workflows folder")
    print("\t3. publish your work")
    print()


workflowscli.add_command(wf)
workflowscli.add_command(history)
# workflowscli.add_command(rq)
workflowscli.add_command(startproject)
