from pathlib import Path

from labfunctions import defaults
from labfunctions.hashes import generate_random
from labfunctions.types import ProjectData
from labfunctions.types.runtimes import BuildCtx, RuntimeData, RuntimeSpec
from labfunctions.utils import secure_filename

from .utils import get_spec_from_file


def make_docker_name(projectid: str, spec: RuntimeSpec) -> str:
    """
    In the form of
    nbworkflows/[projectid]-[runtime_name]
    """
    return f"{defaults.DOCKER_AUTHOR}/{projectid}-{spec.name}"


def local_spec2runtime(projectid: str, spec: RuntimeSpec, version: str) -> RuntimeData:
    rid = f"{projectid}/{spec.name}/{version}"
    docker_name = make_docker_name(projectid, spec)

    rd = RuntimeData(
        runtimeid=rid,
        spec=spec,
        runtime_name=spec.name,
        docker_name=docker_name,
        project_id=projectid,
        version=version,
        registry=spec.registry,
    )
    return rd


def local_runtime_data(
    projectid, spec_name="default", runtimes_file="runtimes.yaml", version="latest"
) -> RuntimeData:
    spec = get_spec_from_file(spec_name, runtimes_file)
    rd = local_spec2runtime(projectid, spec, version)
    return rd


def execid_for_build(size=defaults.EXECID_LEN):
    return f"bld{generate_random(size)}"


def build_upload_uri(projectid, runtime_name, version) -> str:
    _name = f"{runtime_name}.{version}.zip"
    name = secure_filename(_name)
    root = Path(projectid)

    uri = str(root / defaults.PROJECT_UPLOADS / name)
    return uri


def create_build_ctx(
    projectid: str,
    spec: RuntimeSpec,
    version: str,
    project_store_class: str,
    project_store_bucket: str,
    registry=None,
) -> BuildCtx:
    _id = execid_for_build()
    uri = build_upload_uri(projectid, spec.name, version)
    docker = make_docker_name(projectid, spec)
    dockerfile = f"Dockerfile.{spec.name}"
    zip_name = uri.split("/")[-1]
    return BuildCtx(
        projectid=projectid,
        spec=spec,
        docker_name=docker,
        version=version,
        dockerfile=dockerfile,
        zip_name=zip_name,
        download_zip=uri,
        execid=_id,
        project_store_class=project_store_class,
        project_store_bucket=project_store_bucket,
        registry=registry,
    )
