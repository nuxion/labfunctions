import json
import logging
from io import BytesIO

import docker

from .types import DockerBuildLog, DockerBuildLowLog, DockerPushLog


def _open_dockerfile(dockerfile):
    with open(dockerfile, "rb") as f:
        obj = f.read()
    return BytesIO(obj)


def docker_build(path, dockerfile, tag, rm=False, push=False) -> DockerBuildLog:
    """Build docker
    :param path: path to the Dockerfile
    :param dockerfile: name of the Dockerfile
    :param tag: fullname of the dokcer image to build
    :param rm: remove intermediate build images
    :param push: Push docker image to a repository
    """

    error = False

    build_log = docker_low_build(path, dockerfile, tag, rm)
    push_log = None
    if push:
        push_log = docker_push_image(tag)

    if build_log.error or push_log.error:
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
