import click
import requests
import toml

from nb_workflows.conf import Config
from nb_workflows.workflows import client
from nb_workflows.workflows.entities import NBTask, ScheduleData


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
    "action", type=click.Choice(["init", "push", "list", "exec", "delete"])
)
def workflows(from_file, web, jobid, remote, action):
    """Manage workflows"""

    if action == "init":
        if remote:
            c = client.from_remote(web)
            c.write()
        else:
            c = client.init(from_file)
            c.write()

    elif action == "push":
        c = client.from_file(from_file)
        c.push_all()

    elif action == "list":
        c = client.from_file(from_file)
        data = c.list_scheduled()
        print("\nnb_name | jobid | description | is_enabled\n")
        for d in data:
            print(f"{d.nb_name} | {d.jobid} | {d.description} | [{d.enabled}]")

    elif action == "exec":
        c = client.from_file(from_file)
        rsp = c.execute_remote(jobid)
        if rsp.status_code == 202:
            print(f"Jobid: {jobid}, scheduled.")
            print(f"Executionid: {rsp.executionid}")

    elif action == "delete":
        c = client.from_file(from_file)
        rsp = c.delete(jobid)
        print(f"Jobid: {jobid}, deleted. Code {rsp}")

    else:
        print("Valid actions are: [init, push, list, exec, delete]")
