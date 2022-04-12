import click
from rich.console import Console

from nb_workflows import defaults
from nb_workflows.conf import load_client

console = Console()


@click.group(name="cluster")
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
def clustercli(ctx, url_service, from_file):
    """
    Execute workflows or notebooks, locally or remote
    """
    ctx.ensure_object(dict)

    ctx.obj["URL"] = url_service
    ctx.obj["WF_FILE"] = from_file


@clustercli.command(name="create-node")
@click.option("--provider", "-p", default="gcloud", help="Cloud to run")
@click.argument("name")
@click.pass_context
def create(ctx, wfid):
    """It will run the task inside a docker container, it exist only as a tester"""

    url_service = ctx.obj["URL"]
    from_file = ctx.obj["WF_FILE"]
