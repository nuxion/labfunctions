import sys
from datetime import datetime
from typing import Optional

import click
import redis
from rich import print_json
from rich.prompt import Confirm
from rich.table import Table

from labfunctions import client, cluster, defaults

# from labfunctions.errors.cluster import ClusterSpecNotFound
from labfunctions.utils import format_seconds

from .utils import ConfigCli, console, progress

cliconf = ConfigCli()
URL = cliconf.data.url_service
LF = cliconf.data.lab_file


@click.group(name="cluster")
def clustercli():
    """
    Manage instances and agents
    """
    pass


@clustercli.command(name="create-instance")
@click.option(
    "--deploy",
    "-D",
    is_flag=True,
    default=True,
    help="If used, then a agent will be deployed",
)
@click.option("--qnames", "-q", default="cpu", help="Queues separated with commas ','")
@click.option(
    "--agent-image",
    "-a",
    default="nuxion/labfunctions:latest",
    help="Docker image with version, to use as agent",
)
@click.option(
    "--cluster-name", "-C", default="default", help="Cluster where it should run"
)
@click.option("--timeout", "-t", default="15m", help="Timeout of the task to complete")
@click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
def create_instancecli(cluster_name, deploy, use_public, qnames, agent_image, timeout):
    """It will create a new instance in the cluster choosen"""
    nbclient = client.from_file(url_service=URL)

    di = agent_image.split(":")[0]
    dv = agent_image.split(":")[1]
    q = qnames.split(",")
    req = cluster.CreateRequest(
        cluster_name=cluster_name,
        agent=cluster.DeployAgentRequest(
            qnames=q,
            use_public=use_public,
            docker_image=di,
            docker_version=dv,
            worker_procs=5,
        ),
        timeout=timeout,
    )
    jobid = nbclient.cluster_create_instance(req)
    console.print(f"Create instance task sent with id [magenta]{jobid}[/]")


@clustercli.command(name="destroy-instance")
@click.option("--cluster", "-C", default="default", help="Cluster where it will run")
@click.argument("machine")
def destroy_instance(machine, cluster):
    """Destroy a instance by name"""

    nbclient = client.from_file(None, url_service=URL)
    jobid = nbclient.cluster_destroy_instance(cluster, machine=machine)
    if jobid:
        console.print(
            f"Destroy task sent for instance {machine} with id [magenta]{jobid}[/]"
        )
    else:
        console.print(f"[yellow]{machine} not found[/]")


@clustercli.command(name="list-instances")
@click.option(
    "--cluster-name", "-C", default="default", help="list instances from cluster"
)
def list_instances(cluster_name):
    """List instances in a cluster"""
    table = Table()
    table.add_column("Name", justify="left", style="cyan")

    nbclient = client.from_file(None, url_service=URL)
    nodes = nbclient.cluster_list_instances(cluster_name)
    for n in nodes:
        table.add_row(
            n,
        )
    console.print(table)


@clustercli.command(name="specs")
def list_specs():
    """Get specs definitions"""
    nbclient = client.from_file(None, url_service=URL)
    specs = nbclient.cluster_get_specs()
    print_json(data=[s.dict() for s in specs])
