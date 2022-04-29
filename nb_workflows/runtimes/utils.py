from pathlib import Path
from typing import Any, Dict, Optional, Union

from nb_workflows import defaults
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.types.runtimes import DockerSpec, RuntimeSpec
from nb_workflows.utils import execute_cmd, open_yaml


def generate_dockerfile(dst_root: Path, runtime: RuntimeSpec):
    render_to_file(
        runtime.container.base_template,
        str((dst_root / f"Dockerfile.{runtime.name}").resolve()),
        data=runtime.container.dict(),
    )


def get_from_file(name: str, from_file="runtimes.yaml") -> RuntimeSpec:
    data = open_yaml(from_file)
    spec_data = data["runtimes"][name]
    spec = RuntimeSpec(name=name, **spec_data)
    return spec


def git_short_head_id():
    return execute_cmd("git rev-parse --short HEAD")


def git_last_tag():
    return execute_cmd("git describe --tags")
