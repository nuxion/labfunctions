import json
import logging
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx

import docker
from nb_workflows import client, defaults
from nb_workflows.conf import load_server
from nb_workflows.types import ProjectData, ServerSettings
from nb_workflows.types.docker import DockerBuildLog, DockerBuildLowLog, DockerPushLog
from nb_workflows.types.runtimes import BuildCtx, RuntimeReq


def docker_build(
    path, dockerfile, tag, version, rm=False, push=False
) -> DockerBuildLog:
    """Build docker
    :param path: path to the Dockerfile
    :param dockerfile: name of the Dockerfile
    :param tag: fullname of the dokcer image to build
    :param rm: remove intermediate build images
    :param push: Push docker image to a repository
    """

    error = False
    error_build = False
    error_push = False

    client = docker.from_env()

    build_log = docker_low_build(path, dockerfile, tag, rm)
    if not build_log.error:
        img = client.images.get(tag)
        img.tag(tag, tag=version)

    error_build = build_log.error

    push_log = None
    if push:
        # push_log = docker_push_image(tag)
        push_log = docker_push_image(f"{tag}:{version}")
        error_push = push_log.error

    if error_build or error_push:
        error = True

    return DockerBuildLog(build_log=build_log, push_log=push_log, error=error)


def docker_push_image(tag) -> DockerPushLog:

    dock = docker.from_env()
    error = False
    try:
        push_log_str = dock.images.push(tag)
    except docker.errors.APIError as e:
        error = True
        push_log_str = str(e)

    return DockerPushLog(logs=push_log_str, error=error)


def docker_low_build(path, dockerfile, tag, rm=False) -> DockerBuildLowLog:
    """It uses the low API of python sdk.
    :param path: path to the Dockerfile
    :param dockerfile: name of the Dockerfile
    :param tag: fullname of the dokcer image to build
    :param rm: remove intermediate build images
    """

    # obj = _open_dockerfile(dockerfile)
    # build(fileobj=obj...
    _client = docker.APIClient(base_url="unix://var/run/docker.sock")
    generator = _client.build(path=path, dockerfile=dockerfile, tag=tag, rm=rm)
    error = False
    log = ""
    while True:
        try:
            output = generator.__next__()
            output = output.decode().strip("\r\n")
            json_output = json.loads(output)
            if "stream" in json_output:
                logging.info(json_output["stream"].strip("\n"))
                log += json_output["stream"]
            elif "errorDetail" in json_output:
                logging.error(json_output["error"])
                log += json_output["error"]
                error = True

        except StopIteration:
            logging.info("Docker image build complete.")
            log += "Docker image build complete.\n"
            break
        except ValueError:
            logging.info("Error parsing output from docker image build: %s" % output)
            log += "Error parsing output from docker image build:{output}\n"
            # raise ValueError(log)
            error = True

    return DockerBuildLowLog(error=error, logs=log)


def _extract_project(project_zip_file, dst_dir):
    with ZipFile(project_zip_file, "r") as zo:
        zo.extractall(dst_dir)


def _download_zip_project(ctx: BuildCtx, project_dir):

    # uri = f"{settings.FILESERVER}/{settings.FILESERVER_BUCKET}/{ctx.project_zip_route}"
    uri = ctx.download_zip
    with open(project_dir / ctx.zip_name, "wb") as f:
        with httpx.stream("GET", uri, timeout=100) as r:
            for chunk in r.iter_raw():
                f.write(chunk)


def prepare_files(ctx: BuildCtx, settings: ServerSettings):

    root = Path(settings.BASE_PATH)
    project_dir = root / settings.AGENT_DATA_FOLDER / ctx.projectid / "build"
    project_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = project_dir / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    _download_zip_project(ctx, project_dir)
    _extract_project(project_dir / ctx.zip_name, temp_dir)

    return project_dir, temp_dir


def builder_exec(ctx: BuildCtx):
    """It's in charge of building docker images for projects"""

    settings = load_server()

    nb_client = client.agent(
        url_service=settings.WORKFLOW_SERVICE,
        token=settings.AGENT_TOKEN,
        refresh=settings.AGENT_REFRESH_TOKEN,
        projectid=ctx.projectid,
    )
    project_dir, tmp_dir = prepare_files(ctx, settings)

    # pd = nb_client.projects_get()
    docker_tag = ctx.docker_name
    push = False
    if ctx.registry:
        docker_tag = f"{ctx.registry}/{docker_tag}"
        push = True

    nb_client.events_publish(
        ctx.execid, f"Starting build for {docker_tag}", event="log"
    )
    logs = docker_build(
        f"{tmp_dir}/src",
        f"{ctx.dockerfile}",
        tag=docker_tag,
        version=ctx.version,
        push=push,
    )
    req = RuntimeReq(
        runtime_name=ctx.spec.name,
        docker_name=ctx.docker_name,
        spec=ctx.spec,
        project_id=ctx.projectid,
        version=ctx.version,
        registry=ctx.registry,
    )
    nb_client.runtime_create(req)

    nb_client.events_publish(ctx.execid, data="finished", event="result")
    nb_client.events_publish(ctx.execid, data="exit", event="control")

    return logs
