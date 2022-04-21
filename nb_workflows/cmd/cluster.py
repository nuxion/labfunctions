import sys
from datetime import datetime
from typing import Optional

import click
import redis
from rich import print_json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn
from rich.prompt import Confirm
from rich.table import Table

from nb_workflows import defaults
from nb_workflows.cluster import (
    ClusterControl,
    Inventory,
    ProviderSpec,
    machine_from_settings,
)
from nb_workflows.conf import load_client
from nb_workflows.conf.server_settings import settings
from nb_workflows.control_plane.register import AgentRegister
from nb_workflows.errors.cluster import ClusterSpecNotFound
from nb_workflows.utils import format_seconds

console = Console()
progress = Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
)


def create_cluster_control(
    from_file: str, cluster: Optional[str] = None
) -> ClusterControl:
    cluster_file = ClusterControl.load_cluster_file(from_file)
    try:
        cluster = cluster or cluster_file.default_cluster
        spec = cluster_file.clusters[cluster]
    except KeyError:
        console.print(f"[bold red] Cluster {cluster} not found in {from_file}")
        console.print(f"Clusters availables: {list(cluster_file.clusters.keys())}")
        raise ClusterSpecNotFound(cluster, from_file)

    inventory = Inventory(cluster_file.inventory)
    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    registry = AgentRegister(rdb, cluster)
    cc = ClusterControl(registry, spec=spec, inventory=inventory)
    return cc


@click.group(name="cluster")
def clustercli():
    """
    Execute workflows or notebooks, locally or remote
    """
    pass


@clustercli.command(name="create-machine")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option(
    "--deploy",
    "-D",
    is_flag=True,
    default=False,
    help="If used, then a agent will be deployed",
)
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
@click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
@click.option("--deploy-local", "-L", is_flag=True, default=False, help="Run locally")
def create_machinecli(from_file, cluster, deploy, use_public, deploy_local):
    """It will create a new machine in a provider choosen, inside of a cluster"""

    try:
        cc = create_cluster_control(from_file, cluster)
        console.print(
            f"=> Creating a new machine for cluster [magenta bold]{cc.cluster_name}[/]"
        )
    except ClusterSpecNotFound:
        sys.exit(-1)

    driver = cc.get_provider()
    instance = cc.create_instance(driver, settings, deploy, use_public, deploy_local)
    print_json(data=instance.dict())


@clustercli.command(name="destroy-machine")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
@click.argument("machine-name")
def destroy_machinecli(from_file, machine_name, cluster):
    """Destroy a machine by name"""

    try:
        cc = create_cluster_control(from_file, cluster)
        console.print(
            f"=> Destroying [magenta bold]{machine_name}[/] in "
            f"[cyan bold]{cc.cluster_name}[/]"
        )
    except ClusterSpecNotFound:
        sys.exit(-1)

    driver = cc.inventory.get_provider(cc.spec.provider)
    cc.destroy_instance(driver, machine_name)
    console.print(f"[green bold]{machine_name}[/] [green]destroyed[/]")


@clustercli.command(name="list-machines")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--tags", "-T", default="nbworkflows", help="Tags separated by comma")
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
@click.option(
    "--filter-by-cluster",
    "-F",
    is_flag=True,
    default=True,
    help="Filter nodes by cluster",
)
def list_machinescli(from_file, tags, cluster, filter_by_cluster):
    """List machines in a cluster"""
    try:
        cc = create_cluster_control(from_file, cluster)
    except ClusterSpecNotFound:
        sys.exit(-1)

    driver = cc.inventory.get_provider(cc.spec.provider)

    nodes = driver.list_machines(tags=tags.split(","))
    title = "Machines"
    if filter_by_cluster:
        filtered = [n for n in nodes if n.labels["cluster"] == cc.cluster_name]
        title = f"Machines for cluster {cc.cluster_name}"
        nodes = filtered
    table = Table(title=title)
    table.add_column("Name", justify="left", style="red")
    table.add_column("Location", justify="center", style="cyan")
    table.add_column("Private", justify="center", style="cyan")
    table.add_column("Public", style="cyan", justify="center")
    table.add_column("Cluster", style="red", justify="right")
    for n in nodes:
        table.add_row(
            n.machine_name,
            n.location,
            n.private_ips[0],
            n.public_ips[0],
            n.labels["cluster"],
        )
    console.print(table)


@clustercli.command(name="up")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
@click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
@click.option("--deploy-local", "-L", is_flag=True, default=False, help="Run locally")
def upcli(from_file, use_public, deploy_local, cluster):
    """Create a cluster"""
    try:
        cc = create_cluster_control(from_file, cluster)
    except ClusterSpecNotFound:
        sys.exit(-1)

    driver = cc.inventory.get_provider(cc.spec.provider)

    with progress:
        progress.add_task(f"Starting {cc.cluster_name}...", start=False)
        cc.scale(driver, settings, use_public=use_public, deploy_local=deploy_local)

    console.print(f"=> [green bold]Cluster {cc.cluster_name} started[/]")


@clustercli.command(name="destroy")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--cluster", "-C", default=None, help="Cluster where it will run")
@click.option(
    "--hard", is_flag=True, default=False, help="if true it destroy machines directly"
)
def destroycli(from_file, cluster, hard):
    """Destroy a cluster"""
    try:
        cc = create_cluster_control(from_file, cluster)
    except ClusterSpecNotFound:
        sys.exit(-1)

    driver = cc.inventory.get_provider(cc.spec.provider)

    with progress:
        progress.add_task(f"Destroying cluster {cc.cluster_name}")
        if hard:
            nodes = driver.list_machines(tags=[defaults.CLOUD_TAG])
            filtered = [n for n in nodes if n.labels["cluster"] == cluster]
            for n in filtered:
                progress.add_task(f"Destroying {n.machine_name}")
                driver.destroy_machine(n)
        else:
            agents = cc.register.list_agents(cluster)
            for agt in agents:
                progress.add_task(f"Destroying {agt}")
                cc.destroy_instance(driver, agt)
    console.print(
        f"[bold]Cluster [magenta bold]{cc.cluster_name}[/magenta bold] destroyed[/]"
    )


@clustercli.command(name="list-agents")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--provider", "-p", default="gce", help="Cloud to run")
@click.option("--cluster", "-C", default=None, help="Cluster")
def list_agentscli(from_file, provider, cluster):
    """List agents by cluster"""

    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    ar = AgentRegister(rdb, cluster)

    agents = ar.list_agents(from_cluster=cluster)
    title = "Agents"
    if cluster:
        title = f"Agents for {cluster}"
    table = Table(title=title)
    table.add_column("Name", justify="left", style="cyan")
    table.add_column("Queues", justify="center", style="cyan")
    table.add_column("Cluster", justify="center", style="red")
    table.add_column("Started", style="red", justify="right")

    now = datetime.utcnow().timestamp()
    for agt in agents:
        _agt = ar.get(agt)
        elapsed = now - _agt.birthday
        table.add_row(
            _agt.name, ",".join(_agt.qnames), _agt.cluster, format_seconds(elapsed)
        )
    console.print(table)


@clustercli.command(name="list-clusters")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--cluster", "-C", default=None, help="Cluster")
def list_clusters(from_file, cluster):
    """It will run the task inside a docker container, it exist only as a tester"""

    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    ar = AgentRegister(rdb, cluster)

    clusters = ar.list_clusters()
    title = "Clusters"
    table = Table(title=title)
    table.add_column("Name", justify="left", style="cyan")
    for c in clusters:
        table.add_row(c)
    console.print(table)


@clustercli.command(name="catalog")
@click.option(
    "--from-file",
    "-f",
    default=settings.CLUSTER_SPEC,
    help="yaml file with the configuration",
)
@click.option("--provider", "-p", default=None, help="From a provider")
def catalogcli(from_file, provider):
    """List machine types"""
    try:
        cc = create_cluster_control(from_file)
    except ClusterSpecNotFound:
        sys.exit(-1)

    inventory = cc.inventory

    title = "Machines types"
    table = Table(title=title)
    table.add_column("name", justify="left", style="cyan")
    table.add_column("provider", justify="center", style="blue")
    table.add_column("location", justify="center", style="blue")
    table.add_column("size", justify="right", style="blue")
    for _, m in inventory.machines.items():
        if provider:
            if m.provider == provider:
                table.add_row(m.name, m.provider, m.location, m.machine_type.size)
        else:
            table.add_row(m.name, m.provider, m.location, m.machine_type.size)
    console.print(table)
