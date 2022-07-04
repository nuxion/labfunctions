import sys
from datetime import datetime
from typing import Optional

import click
import redis
from rich import print_json
from rich.prompt import Confirm
from rich.table import Table

from labfunctions import client, cluster, defaults
from labfunctions.conf.server_settings import settings

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
    "--from-file",
    "-f",
    default=None,
    help="yaml file with instance request information",
)
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
@click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
def create_instancecli(
    from_file, cluster_name, deploy, use_public, qnames, agent_image
):
    """It will create a new instance in the cluster choosen"""
    nbclient = client.from_file(from_file, url_service=URL)

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
    )
    jobid = nbclient.cluster_create_instance(req)
    console.print(f"Create instance task sent with id [magenta]{jobid}[/]")


@clustercli.command(name="destroy-instance")
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
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
@click.option("--cluster-name", "-C", default=None, help="list instances from cluster")
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


#
#
# @clustercli.command(name="up")
# @click.option(
#    "--from-file",
#    "-f",
#    default=settings.CLUSTER_SPEC,
#    help="yaml file with the configuration",
# )
# @click.option("--cluster", "-C", default=None, help="Cluster where it will run")
# @click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
# @click.option("--deploy-local", "-L", is_flag=True, default=False, help="Run locally")
# @click.option("--do-deploy", "-D", is_flag=True, default=True, help="Deploy agent")
# def upcli(from_file, use_public, deploy_local, cluster, do_deploy):
#    """Create a cluster"""
#    try:
#        cc = create_cluster_control(from_file, settings.RQ_REDIS, cluster)
#    except ClusterSpecNotFound as e:
#        console.print(f"[bold red]{e}[/]")
#        sys.exit(-1)
#
#    with progress:
#        progress.add_task(f"Starting {cc.cluster_name}...", start=False)
#        cc.scale(
#            settings,
#            use_public=use_public,
#            deploy_local=deploy_local,
#            do_deploy=do_deploy,
#        )
#
#    console.print(f"=> [green bold]Cluster {cc.cluster_name} started[/]")
#
#
# @clustercli.command(name="destroy")
# @click.option(
#    "--from-file",
#    "-f",
#    default=settings.CLUSTER_SPEC,
#    help="yaml file with the configuration",
# )
# @click.option("--cluster", "-C", default=None, help="Cluster where it will run")
# @click.option(
#    "--hard", is_flag=True, default=False, help="if true it destroy machines directly"
# )
# def destroycli(from_file, cluster, hard):
#    """Destroy a cluster"""
#    try:
#        cc = create_cluster_control(from_file, settings.RQ_REDIS, cluster)
#    except ClusterSpecNotFound as e:
#        console.print(f"[bold red]{e}[/]")
#        sys.exit(-1)
#
#    with progress:
#        progress.add_task(f"Destroying cluster {cc.cluster_name}")
#        if hard:
#            nodes = cc.provider.list_machines(
#                location=cc.spec.location, tags=[defaults.CLOUD_TAG]
#            )
#            filtered = [n for n in nodes if n.labels["cluster"] == cluster]
#            for n in filtered:
#                progress.add_task(f"Destroying {n.machine_name}")
#                cc.provider.destroy_machine(n)
#        else:
#            agents = cc.register.list_agents(cluster)
#            for agt in agents:
#                progress.add_task(f"Destroying {agt}")
#                cc.destroy_instance(agt)
#    console.print(
#        f"[bold]Cluster [magenta bold]{cc.cluster_name}[/magenta bold] destroyed[/]"
#    )
#
#
# @clustercli.command(name="list-agents")
# @click.option(
#    "--from-file",
#    "-f",
#    default=settings.CLUSTER_SPEC,
#    help="yaml file with the configuration",
# )
# @click.option("--provider", "-p", default="gce", help="Cloud to run")
# @click.option("--cluster", "-C", default=None, help="Cluster")
# def list_agentscli(from_file, provider, cluster):
#    """List agents by cluster"""
#
#    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
#    ar = AgentRegister(rdb, cluster)
#
#    agents = ar.list_agents(from_cluster=cluster)
#    title = "Agents"
#    if cluster:
#        title = f"Agents for {cluster}"
#    table = Table(title=title)
#    table.add_column("Name", justify="left", style="cyan")
#    table.add_column("Queues", justify="center", style="cyan")
#    table.add_column("Cluster", justify="center", style="red")
#    table.add_column("Started", style="red", justify="right")
#
#    now = datetime.utcnow().timestamp()
#    for agt in agents:
#        _agt = ar.get(agt)
#        elapsed = now - _agt.birthday
#        table.add_row(
#            _agt.name, ",".join(
#                _agt.qnames), _agt.cluster, format_seconds(elapsed)
#        )
#    console.print(table)
#
#
# @clustercli.command(name="list-clusters")
# @click.option(
#    "--from-file",
#    "-f",
#    default=settings.CLUSTER_SPEC,
#    help="yaml file with the configuration",
# )
# @click.option("--cluster", "-C", default=None, help="Cluster")
# def list_clusters(from_file, cluster):
#    """It will run the task inside a docker container, it exist only as a tester"""
#
#    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
#    ar = AgentRegister(rdb, cluster)
#
#    clusters = ar.list_clusters()
#    title = "Clusters"
#    table = Table(title=title)
#    table.add_column("Name", justify="left", style="cyan")
#    for c in clusters:
#        table.add_row(c)
#    console.print(table)
#
#
# @clustercli.command(name="catalog")
# @click.option(
#    "--from-file",
#    "-f",
#    default=settings.CLUSTER_SPEC,
#    help="yaml file with the configuration",
# )
# @click.option("--provider", "-p", default=None, help="From a provider")
# def catalogcli(from_file, provider):
#    """List machine types"""
#
#    try:
#        cc = create_cluster_control(from_file, settings.RQ_REDIS)
#    except ClusterSpecNotFound as e:
#        console.print(f"[bold red]{e}[/]")
#        sys.exit(-1)
#
#    inventory = cc.inventory
#
#    title = "Machines types"
#    table = Table(title=title)
#    table.add_column("name", justify="left", style="cyan")
#    table.add_column("provider", justify="center", style="blue")
#    table.add_column("location", justify="center", style="blue")
#    table.add_column("size", justify="right", style="blue")
#    for _, m in inventory.machines.items():
#        if provider:
#            if m.provider == provider:
#                table.add_row(m.name, m.provider, m.location,
#                              m.machine_type.size)
#        else:
#            table.add_row(m.name, m.provider, m.location, m.machine_type.size)
#    console.print(table)
