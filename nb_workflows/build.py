import json
import logging
from io import BytesIO
from zipfile import ZipFile

import docker
from nb_workflows.conf import defaults
from nb_workflows.types import ProjectData
from nb_workflows.types.docker import DockerBuildLog, DockerBuildLowLog, DockerPushLog


def _open_dockerfile(dockerfile):
    with open(dockerfile, "rb") as f:
        obj = f.read()
    return BytesIO(obj)


def generate_docker_name(pd: ProjectData, docker_version: str):
    # if not pd.username:
    # return f"{pd.name}/{pd.name}:{docker_version}"
    return f"{pd.username.lower()}/{pd.name.lower()}:{docker_version}"


def docker_build(path, dockerfile, tag, rm=False, push=False) -> DockerBuildLog:
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
    if not build_log.error and tag != "current":
        img = client.images.get(tag)
        img.tag(tag, tag="latest")

    error_build = build_log.error

    push_log = None
    if push:
        push_log = docker_push_image(tag)
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


def extract_project(project_zip_file, dst_dir):
    with ZipFile(project_zip_file, "r") as zo:
        zo.extractall(dst_dir)


def make_build(project_zip_file, tag, temp_dir="/tmp/zip/") -> DockerBuildLowLog:
    extract_project(project_zip_file, temp_dir)
    logs = docker_build(f"{temp_dir}/src", defaults.DOCKERFILE_RUNTIME_NAME, tag=tag)
    return logs
