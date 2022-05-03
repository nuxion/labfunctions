import json
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

import docker
from nb_workflows.utils import mkdir_p


class CommandResources(BaseModel):
    mem_limit: Optional[int] = None
    mem_reservation: Optional[int] = None


class CommandVolume(BaseModel):
    orig_mount: str
    dst_mount: str
    extra: Dict[str, Any] = {}


class CommandResult(BaseModel):
    msg: str
    status: int


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
        resources=CommandResources(),
        volumes: List[CommandVolume] = [],
    ) -> CommandResult:

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
            if remove:
                container.remove()
            logs = container.logs().decode("utf-8")
        except docker.errors.ContainerError as e:
            logs = str(e)
            status_code = -2
        except docker.errors.APIError as e:
            logs = str(e)
            status_code = -3
        return CommandResult(msg=logs, status=status_code)
