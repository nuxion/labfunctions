import json
import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

import docker
from labfunctions import log
from labfunctions.types.docker import (
    DockerBuildLog,
    DockerBuildLowLog,
    DockerPushLog,
    DockerResources,
    DockerRunResult,
    DockerVolume,
)
from labfunctions.utils import mkdir_p


def shell(
    command: str, check=True, input=None, cwd=None, silent=False, env=None
) -> subprocess.CompletedProcess:
    """
    Runs a provided command, streaming its output to the log files.
    :param command: A command to be executed, as a single string.
    :param check: If true, will throw exception on failure (exit code != 0)
    :param input: Input for the executed command.
    :param cwd: Directory in which to execute the command.
    :param silent: If set to True, the output of command won't be logged or printed.
    :param env: A set of environment variable for the process to use. If None, the current env is inherited.
    :return: CompletedProcess instance - the result of the command execution.
    """
    if not silent:
        log_msg = "Executing: {command}"
        # log_msg = (
        #     f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        #     f"Executing: {command}" + os.linesep
        # )
        # print(log_msg)
        # print(log_msg)
        log.client_logger.info(log_msg)

    proc = subprocess.run(
        shlex.split(command),
        check=check,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        input=input,
        cwd=cwd,
        env=env,
    )

    if not silent:
        log.error_logger.error(proc.stderr.decode())
        log.client_logger.info(proc.stdout.decode())
        # print(proc.stderr.decode())
        # print(proc.stdout.decode())

    return proc


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
    log_messages = ""
    while True:
        try:
            output = generator.__next__()
            output = output.decode().strip("\r\n")
            json_output = json.loads(output)
            if "stream" in json_output:
                log.client_logger.info(json_output["stream"].strip("\n"))
                log_messages += json_output["stream"]
            elif "errorDetail" in json_output:
                log.error_logger.error(json_output["error"])
                log_messages += json_output["error"]
                error = True

        except StopIteration:
            log.client_logger.info("Docker image build complete")
            log_messages += "Docker image build complete.\n"
            break
        except ValueError:
            log.client_logger.info(
                "Error parsing output from docker image build: %s" % output
            )
            log_messages += "Error parsing output from docker image build:{output}\n"
            # raise ValueError(log)
            error = True

    return DockerBuildLowLog(error=error, logs=log_messages)


class DockerCommand:
    __slots__ = "docker"

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
        *,
        timeout: int = 120,
        env_data: Dict[str, Any] = {},
        remove: bool = True,
        require_gpu: bool = False,
        network_mode: str = "bridge",
        ports=None,
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
                network_mode=network_mode,
                ports=ports,
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
            log.error_logger.error(str(e))
            logs = str(e)
            status_code = -2
        except docker.errors.APIError as e:
            logs = str(e)
            log.error_logger.error(str(e))
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
            log.error_logger.error(str(e))
            push_log_str = str(e)

        return DockerPushLog(logs=push_log_str, error=error)
