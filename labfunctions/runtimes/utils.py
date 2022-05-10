from pathlib import Path
from typing import Any, Dict, Optional, Union

from labfunctions import defaults
from labfunctions.conf.jtemplates import get_package_dir, render_to_file
from labfunctions.types.runtimes import DockerSpec, RuntimeData, RuntimeSpec
from labfunctions.utils import execute_cmd, open_yaml


def generate_dockerfile(dst_root: Path, runtime: RuntimeSpec):
    render_to_file(
        runtime.container.base_template,
        str((dst_root / f"Dockerfile.{runtime.name}").resolve()),
        data=runtime.container.dict(),
    )


def get_runtimes_specs(from_file="runtimes.yaml") -> Dict[str, RuntimeSpec]:
    data = open_yaml(from_file)
    runtimes = {k: RuntimeSpec(name=k, **v) for k, v in data["runtimes"].items()}
    return runtimes


def get_spec_from_file(name: str, from_file="runtimes.yaml") -> RuntimeSpec:
    specs = get_runtimes_specs(from_file)
    return specs[name]


def git_short_head_id():
    return execute_cmd("git rev-parse --short HEAD")


def git_last_tag():
    return execute_cmd("git describe --tags")
