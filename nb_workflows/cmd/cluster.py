import sys
from datetime import datetime

import click
import redis
from rich import print_json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn
from rich.table import Table

from nb_workflows import defaults
from nb_workflows.cluster.base import ProviderSpec
from nb_workflows.cluster.context import machine_from_settings
from nb_workflows.cluster.control import ClusterControl
from nb_workflows.cluster.gcloud_provider import GCEProvider
from nb_workflows.cluster.local_provider import LocalProvider
from nb_workflows.conf import load_client
from nb_workflows.conf.server_settings import settings
from nb_workflows.control_plane.register import AgentRegister
from nb_workflows.utils import format_seconds, get_class

providers = {
    "local": "nb_workflows.cluster.local_provider.LocalProvider",
    "gce": "nb_workflows.cluster.gcloud_provider.GCEProvider",
}
console = Console()
progress = Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
)


@click.group(name="cluster")
@click.option(
    "--from-file",
    "-f",
    default="scripts/local_clusters.yaml",
    help="yaml file with the configuration",
)
@click.pass_context
def clustercli(ctx, from_file):
    """
    Execute workflows or notebooks, locally or remote
    """
    ctx.ensure_object(dict)

    ctx.obj["CLUSTERS_FILE"] = from_file


@clustercli.command(name="create-machine")
@click.option("--provider", "-p", default="local", help="Cloud to run")
@click.option("--cluster", "-c", default="cpu", help="Cluster where it will run")
@click.option(
    "--qnames", "-q", default="control,default", help="Cluster where it will run"
)
@click.argument("name")
@click.pass_context
def create_machinecli(ctx, name, provider, cluster, qnames):
    """It will run the task inside a docker container, it exist only as a tester"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    ctx = machine_from_settings(name, cluster, qnames.split(","), settings)
    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    register = AgentRegister(rdb, cluster)
    driver: ProviderSpec = get_class(providers[provider])()
    console.print(f"[magenta bold]Creating {ctx.machine.name}")
    instance = driver.create_machine(ctx.machine)
    register.register_machine(instance)


@clustercli.command(name="destroy-machine")
@click.option("--cluster", "-C", default="default", help="Cluster where it will run")
@click.argument("name")
@click.pass_context
def destroy_nodecli(ctx, name, cluster):
    """It will run the task inside a docker container, it exist only as a tester"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    clusters = ClusterControl.load_spec(from_file)
    try:
        spec = clusters[cluster]
    except KeyError:
        console.print(f"[bold red] Cluster {name} not found in {from_file}")
        console.print(f"Clusters availables: {clusters.keys()}")
        sys.exit(-1)
    prov = providers[spec.provider]
    driver: ProviderSpec = get_class(prov)()
    rdb = redis.from_url(settings.RQ_REDIS)
    control = ClusterControl(rdb, spec)
    control.destroy_instance(driver, name)
    # console.print(f"[magenta bold]Machine {name} unregistered[/]")


@clustercli.command(name="list-machines")
@click.option("--tags", "-T", default=None, help="Tags")
@click.option("--cluster", "-C", default="default", help="Cluster where it will run")
@click.pass_context
def list_nodecli(ctx, tags, cluster):
    """It will run the task inside a docker container, it exist only as a tester"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    clusters = ClusterControl.load_spec(from_file)
    try:
        spec = clusters[cluster]
    except KeyError:
        console.print(f"[bold red] Cluster {cluster} not found in {from_file}")
        console.print(f"Clusters availables: {clusters.keys()}")
        sys.exit(-1)
    prov = providers[spec.provider]
    driver: ProviderSpec = get_class(prov)()

    nodes = driver.list_machines(tags=tags)
    print_json(data=[n.dict() for n in nodes])


@clustercli.command(name="up")
@click.option("--use-public", "-P", is_flag=True, default=False, help="Use public ip")
@click.option("--deploy-local", "-L", is_flag=True, default=False, help="Run locally")
@click.argument("name")
@click.pass_context
def upcli(ctx, use_public, deploy_local, name):
    """It will create a cluster"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    clusters = ClusterControl.load_spec(from_file)
    try:
        spec = clusters[name]
    except KeyError:
        console.print(f"[bold red] Cluster {name} not found in {from_file}")
        console.print(f"Clusters availables: {clusters.keys()}")
        sys.exit(-1)
    prov = providers[spec.provider]
    driver: ProviderSpec = get_class(prov)()
    rdb = redis.from_url(settings.RQ_REDIS)
    control = ClusterControl(rdb, spec)
    with progress:
        progress.add_task("Scaling cluster...", start=False)
        control.scale(
            driver, settings, use_public=use_public, deploy_local=deploy_local
        )
    console.print("[magenta bold]Cluster started[/]")


@clustercli.command(name="destroy")
@click.argument("name")
@click.pass_context
def destroycli(ctx, name):
    """It will create a cluster"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    clusters = ClusterControl.load_spec(from_file)
    try:
        spec = clusters[name]
    except KeyError:
        console.print(f"[bold red] Cluster {name} not found in {from_file}")
        console.print(f"Clusters availables: {clusters.keys()}")
        sys.exit(-1)
    prov = providers[spec.provider]
    driver: ProviderSpec = get_class(prov)()
    rdb = redis.from_url(settings.RQ_REDIS)
    control = ClusterControl(rdb, spec)
    with progress:
        progress.add_task("Destroying cluster...", start=False)
        agents = control.register.list_agents(name)
        for agt in agents:
            control.destroy_instance(driver, agt)
    console.print("[magenta bold]Cluster destroyed[/]")


@clustercli.command(name="list-agents")
@click.option("--provider", "-p", default="gce", help="Cloud to run")
@click.option("--cluster", "-C", default=None, help="Cluster")
@click.pass_context
def list_agentscli(ctx, provider, cluster):
    """It will run the task inside a docker container, it exist only as a tester"""
    import redis

    from nb_workflows.conf.server_settings import settings
    from nb_workflows.control_plane.register import AgentRegister

    from_file = ctx.obj["CLUSTERS_FILE"]
    rdb = redis.from_url(settings.RQ_REDIS)
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
@click.option("--cluster", "-C", default=None, help="Cluster")
@click.pass_context
def list_clusters(ctx, cluster):
    """It will run the task inside a docker container, it exist only as a tester"""

    from_file = ctx.obj["CLUSTERS_FILE"]
    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    ar = AgentRegister(rdb, cluster)

    clusters = ar.list_clusters()
    title = "Clusters"
    table = Table(title=title)
    table.add_column("Name", justify="left", style="cyan")
    for c in clusters:
        table.add_row(c)
    console.print(table)
