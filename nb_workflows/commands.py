import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

import docker
from nb_workflows.types.docker import (
    DockerBuildLog,
    DockerBuildLowLog,
    DockerPushLog,
    DockerResources,
    DockerRunResult,
    DockerVolume,
)
from nb_workflows.utils import mkdir_p


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


class DockerCommand:
    def __init__(self, docker_client=None):
        self.docker = docker_client or docker.from_env()

    def _wait_result(
        self, container: docker.models.containers.Container, timeout: int
    ) -> Union[Dict[str, Any], None]:
        result = None
        try:
            result = container.wait(timeout=timeout)
        except Exception:
            pass
        return result

    def run(
        self,
        cmd: str,
        image: str,
        timeout: int = 120,
        env_data: Dict[str, Any] = {},
        remove: bool = True,
        require_gpu: bool = False,
        resources=DockerResources(),
        volumes: List[DockerVolume] = [],
    ) -> DockerRunResult:

        runtime = None
        if require_gpu:
            runtime = "nvidia"

        logs = ""
        status_code = -1
        try:
            container = self.docker.containers.run(
                image,
                cmd,
                runtime=runtime,
                detach=True,
                environment=env_data,
                **resources.dict(),
            )
            result = self._wait_result(container, timeout)
            if not result:
                container.kill()
            else:
                status_code = result["StatusCode"]
            logs = container.logs().decode("utf-8")
            if remove:
                container.remove()
        except docker.errors.ContainerError as e:
            logs = str(e)
            status_code = -2
        except docker.errors.APIError as e:
            logs = str(e)
            status_code = -3
        return DockerRunResult(msg=logs, status=status_code)

    def build(
        self, path: str, dockerfile: str, tag: str, version: str, rm=False, push=False
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

        build_log = docker_low_build(path, dockerfile, tag, rm)
        if not build_log.error:
            img = self.docker.images.get(tag)
            img.tag(tag, tag=version)

        error_build = build_log.error

        push_log = None
        if push:
            # push_log = docker_push_image(tag)
            push_log = self.push_image(f"{tag}:{version}")
            error_push = push_log.error

        if error_build or error_push:
            error = True

        return DockerBuildLog(build_log=build_log, push_log=push_log, error=error)

    def push_image(self, tag) -> DockerPushLog:
        """
        Push to docker registry
        :param tag: full name of the docker image to push, it should include
        the registry url
        """

        error = False
        try:
            push_log_str = self.docker.images.push(tag)
        except docker.errors.APIError as e:
            error = True
            push_log_str = str(e)

        return DockerPushLog(logs=push_log_str, error=error)
