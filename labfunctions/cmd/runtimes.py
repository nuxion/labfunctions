import os
import sys
from pathlib import Path

import click
from rich.table import Table

from labfunctions import client, defaults, errors, runtimes, secrets
from labfunctions.conf import load_client
from labfunctions.errors.client import ProjectUploadError
from labfunctions.io.kvspec import GenericKVSpec
from labfunctions.runtimes.builder import builder_exec
from labfunctions.runtimes.context import build_upload_uri, create_build_ctx
from labfunctions.types.runtimes import RuntimeSpec
from labfunctions.utils import execute_cmd, open_yaml

from .utils import ConfigCli, console, progress, watcher

settings = load_client()
cliconf = ConfigCli()
URL = cliconf.data.url_service
WF = cliconf.data.lab_file


@click.group(name="runtimes")
def runtimescli():
    """
    Generates and deploy runtimes

    """


@runtimescli.command()
@click.option(
    "--from-file",
    "-f",
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the NB Workflow Service",
)
@click.option(
    "--env-file",
    "-E",
    default="local.nbvars",
    help="env file to be encrypted",
)
@click.option(
    "--stash",
    "-S",
    is_flag=True,
    default=False,
    help="untracked files are zipped",
)
@click.option(
    "--current",
    "-C",
    is_flag=True,
    default=False,
    help="It will zip all the files ignoring .gitignore =P",
)
@click.option(
    "--only-bundle",
    "-z",
    is_flag=True,
    default=False,
    help="Only generates the bundle file",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="Get events & logs from the executions",
)
@click.option(
    "--local",
    "-L",
    is_flag=True,
    default=False,
    help="Build runtime locally",
)
@click.option(
    "--requirements",
    "-r",
    is_flag=True,
    default=False,
    help="Generates a requirements.txt file base on a pip export",
)
@click.argument("name", default="default")
def build(
    url_service,
    from_file,
    only_bundle,
    env_file,
    current,
    stash,
    watch,
    name,
    local,
    requirements,
):
    """Freeze and build a runtime for your project into the server"""
    c = client.from_file(from_file, url_service)
    # prepare secrets
    try:
        pv = c.get_private_key()
    except errors.PrivateKeyNotFound:
        console.print("[cyan bold]=> Not private key found for this project[/]")
        pv = None
        # sys.exit(-1)

    if requirements:
        execute_cmd("pip3 list --format=freeze > requirements.txt")

    spec = runtimes.get_spec_from_file(name)
    if not spec:
        console.print(f"[red bold](x) Runtime {name} doesn't exists[/]")
        sys.exit(-1)

    console.print(f"=> Bundling runtime [bold magenta]{name}[/]")
    try:
        zfile = runtimes.bundle_project(c.working_area, spec, pv, stash, current)
    except KeyError:
        console.print(
            f"[red bold](x) requirements file missing "
            f"from {spec.container.requirements}[/]"
        )
        sys.exit(-1)
    except TypeError:
        console.print(
            "[red bold](x) There isn't changes in the git repository to perform a "
            "STASH zip file. For untracked files you should add to "
            "the stash the changes, perform: git add .[/]"
        )
        sys.exit(-1)
    except AttributeError:
        console.print(
            "[red bold](x) Bad option: current and stash are different options[/]"
        )
        sys.exit(-1)

    console.print(f"=> Bundle generated in {zfile.filepath}")
    if not only_bundle and not local:
        try:
            c.projects_upload(zfile)
            console.print("[bold green]=> Succesfully uploaded file[/]")
            execid = c.projects_build(spec, zfile.version)
            if not execid:
                console.print("[bold red](x) Error sending build task [/]")
                sys.exit(-1)

            console.print(f"=> Build task sent with execid: [bold magenta]{execid}[/]")
            if watch:
                watcher(c, execid, stats=False)
        except ProjectUploadError:
            console.print("[bold red](x) Error uploading file[/]")
    elif local:
        PROJECTS_STORE_CLASS = "labfunctions.io.kv_local.KVLocal"
        PROJECTS_STORE_BUCKET = "labfunctions"
        os.environ["LF_AGENT_TOKEN"] = c.creds.access_token
        os.environ["LF_AGENT_REFRESH_TOKEN"] = c.creds.refresh_token
        os.environ["LF_RUN_LOCAL"] = "yes"
        kv = GenericKVSpec.create(PROJECTS_STORE_CLASS, PROJECTS_STORE_BUCKET)
        ctx = create_build_ctx(
            c.projectid,
            spec,
            zfile.version,
            PROJECTS_STORE_CLASS,
            PROJECTS_STORE_BUCKET,
        )
        kv.put_stream(ctx.download_zip, kv.from_file_gen(zfile.filepath))
        with progress:
            task = progress.add_task(
                f" Building docker image for {name}", start=False, total=1
            )
            rs = builder_exec(ctx)
            progress.advance(task)
        # rs = builder_exec(ctx)
        # console.print(rs)
        console.print(f"=> Image: [magenta]{ctx.docker_name}:{ctx.version}[/]")
        console.print(f"=> Version: [magenta]{ctx.version}[/]")
        if ctx.registry:
            console.print(f"=> Registry: [magenta]{ctx.registry}[/]")
        if rs.error:
            console.print(
                f"[red bold](x) Error building "
                f"[magenta]{ctx.docker_name}:{ctx.version}[/][/]"
            )
            console.print(f"[red]{rs.build_log.logs}")
        else:
            console.print("[green bold]=> Succesfully[/]")

    # elif action == "agent-token":
    #    creds = c.projects_agent_token()
    #    click.echo(f"access token (keep private): \n{creds.access_token}")

    # elif action == "recreate":
    #     c.projects_create()


@runtimescli.command(name="list")
@click.option(
    "--from-file",
    "-f",
    default=WF,
    help="yaml file with the configuration",
)
@click.option(
    "--url-service",
    "-u",
    default=URL,
    help="URL of the Lab functions service",
)
def listcli(from_file, url_service):
    """List of available runtimes for this project"""
    c = client.from_file(from_file, url_service)
    runtimes = c.runtimes_get_all()
    table = Table(title="Runtimes for the project")
    # table.add_column("alias", style="cyan", no_wrap=True, justify="center")
    table.add_column("runtime_name", style="cyan", justify="center")
    table.add_column("docker_name", style="cyan", justify="center")
    table.add_column("version", style="cyan", justify="center")
    for runtime in runtimes:
        table.add_row(str(runtime.runtime_name), runtime.docker_name, runtime.version)
    console.print(table)


@runtimescli.command()
@click.option(
    "--from-file",
    "-f",
    default="runtimes.yaml",
    help="yaml file with the runtime configuration",
)
@click.argument("name", default="default")
def generate(from_file, name):
    """Render  Dockerfile.[name] based on runtimes.yaml"""
    root = Path(os.getcwd())
    spec = runtimes.get_spec_from_file(name, from_file)
    runtimes.generate_dockerfile(root, spec)
    console.print(f"[green]Dockerfile generated as Dockerfile.{name}[/]")


# @projectcli.command(name="runtimes")
# @click.pass_context
# def runtimescli(ctx):
#     """List of runtimes available for this project"""
#     url_service = ctx.obj["URL"]
#     from_file = ctx.obj["WF_FILE"]
#     c = client.from_file(from_file, url_service)
#     runtimes = c.runtimes_get_all()
#     table = Table(title="Runtimes for the project")
#     # table.add_column("alias", style="cyan", no_wrap=True, justify="center")
#     table.add_column("id", style="cyan", justify="center")
#     table.add_column("docker_name", style="cyan", justify="center")
#     table.add_column("version", style="cyan", justify="center")
#     for runtime in runtimes:
#         table.add_row(str(runtime.id), runtime.docker_name, runtime.version)
#     console.print(table)
#
#
# @projectcli.command(name="list")
# @click.pass_context
# def listcli(ctx):
#     """List of runtimes available for this project"""
#     url_service = ctx.obj["URL"]
#     from_file = ctx.obj["WF_FILE"]
#     c = client.from_file(from_file, url_service)
#
#     projects = c.projects_list()
#
#     table = Table(title="Projects")
#     table.add_column("id", style="cyan", justify="center")
#     table.add_column("name", style="cyan", justify="center")
#     table.add_column("desc", style="yellow", justify="center")
#     for p in projects:
#         table.add_row(p.projectid, p.name, p.description)
#     console.print(table)
#
#
# @projectcli.command()
# @click.pass_context
# def info(ctx):
#     """Project's summary"""
#     url_service = ctx.obj["URL"]
#     c = client.from_file(url_service=url_service)
#     c.info()
