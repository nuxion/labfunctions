
import click
import requests
import toml
from nb_workflows.conf import Config
from nb_workflows.workflows import client
from nb_workflows.workflows.entities import NBTask, ScheduleData


def _get_token(filepath):
    nbc = client.open_config(filepath)
    token = client.get_credentials()
    if token:
        v = client.validate_credentials(nbc.url_service, token)
        if v:
            return token
    return client.login_cli(nbc.url_service)


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
@click.option("--web", default=Config.WORKFLOW_SERVICE, help="Web server")
@click.option("--jobid", "-J", default=None, help="Jobid to execute")
@click.option(
    "--remote", "-r", default=False, is_flag=True, help="execute remote"
)
@click.argument(
    "action", type=click.Choice(["init", "push", "list", "exec", "delete", "login"])
)
def workflows(from_file, web, jobid, remote, action):
    """Manage workflows"""

    if action == "init":
        if remote:
            token = Config.CLIENT_TOKEN or client.login_cli(web)
            c = client.from_remote(web, token)
            c.write()
        else:
            c = client.init(web)
            c.write()

    elif action == "push":
        token = _get_token(from_file)
        c = client.from_file(from_file, token)
        c.push_all()

    elif action == "list":
        token = _get_token(from_file)
        c = client.from_file(from_file, token)
        data = c.list_scheduled()
        print("\nnb_name | jobid | description | is_enabled\n")
        for d in data:
            print(f"{d.nb_name} | {d.jobid} | {d.description} | [{d.enabled}]")

    elif action == "exec":
        token = Config.CLIENT_TOKEN or client.login_cli(web)
        c = client.from_file(from_file, token)
        rsp = c.execute_remote(jobid)
        if rsp.status_code == 202:
            print(f"Jobid: {jobid}, scheduled.")
            print(f"Executionid: {rsp.executionid}")

    elif action == "delete":
        token = Config.CLIENT_TOKEN or client.login_cli(web)
        c = client.from_file(from_file, token)
        rsp = c.delete(jobid)
        print(f"Jobid: {jobid}, deleted. Code {rsp}")

    elif action == "login":
        click.echo(f"\nLogin to NB Workflows services {web}\n")
        token = client.login_cli(web)
        try:
            click.echo(f"ACCESS TOKEN: {token}")
        except KeyError:
            click.echo(f"Error auth, try again")

    else:
        print("Valid actions are: [init, push, list, exec, delete]")


workflowscli.add_command(workflows)
