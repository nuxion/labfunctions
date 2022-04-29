from pathlib import Path
from typing import Any, Dict, Optional, Union

from nb_workflows import defaults
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.types.runtimes import DockerSpec, RuntimeSpec


def generate_dockerfile(dst_root: Path, runtime: RuntimeSpec):
    render_to_file(
        runtime.container.base_template,
        str((dst_root / f"Dockerfile.{runtime.name}").resolve()),
        data=runtime.container.dict(),
    )
