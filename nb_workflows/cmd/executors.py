import os

import click

from nb_workflows import client
from nb_workflows.conf import load_client

settings = load_client()


@click.group()
def executorscli():
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
    default=settings.WORKFLOW_SERVICE,
    help="URL of the NB Workflow Service",
)
@click.option("--jobid", "-J", default=None, help="Jobid to execute")
@click.option("--dev", "-d", default=False, is_flag=True, help="Execute locally")
def exec(from_file, url_service, dev, jobid):
    """Execute workflows. If any jobid is provided, it will look in the environment"""

    from nb_workflows.executors.development import local_dev_exec
    from nb_workflows.executors.local import local_exec_env

    if not dev:
        # TODO: Should be inject or validate url_service param
        # when running from the data plane machine?
        # c = client.nb_from_settings_agent()
        rsp = local_exec_env()
        if rsp:
            click.echo(f"Jobid: {rsp.jobid} locally executed")
            click.echo(f"Executionid: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")
    else:
        c = client.nb_from_file(from_file, url_service=url_service)
        rsp = local_dev_exec(jobid)
        if rsp:
            click.echo(f"Jobid: {rsp.jobid} locally executed")
            click.echo(f"Executionid: {rsp.execid}")
            status = "OK"
            if rsp.error:
                status = "ERROR"
            click.echo(f"Status: {status}")


executorscli.add_command(exec)
