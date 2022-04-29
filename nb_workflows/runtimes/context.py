from pathlib import Path

from nb_workflows import defaults
from nb_workflows.hashes import generate_random
from nb_workflows.types import ProjectData
from nb_workflows.types.runtimes import BuildCtx, RuntimeSpec
from nb_workflows.utils import secure_filename


def docker_name(pd: ProjectData, spec: RuntimeSpec) -> str:
    """
    In the form of
    nbworkflows/[projectid]-[runtime_name]
    """
    return f"{defaults.DOCKER_AUTHOR}/{pd.projectid}-{spec.name}"


def execid_for_build(size=defaults.EXECID_LEN):
    return f"bld.{generate_random(size)}"


def build_upload_uri(projectid, runtime_name, version) -> str:
    _name = f"{runtime_name}.{version}.zip"
    name = secure_filename(_name)
    root = Path(projectid)

    uri = str(root / defaults.PROJECT_UPLOADS / name)
    return uri


def create_build_ctx(
    pd: ProjectData, spec: RuntimeSpec, version, registry=None
) -> BuildCtx:
    _id = execid_for_build()
    uri = build_upload_uri(pd.projectid, spec.name, version)
    docker = docker_name(pd, spec)
    dockerfile = f"Dockerfile.{spec.name}"

    zip_name = uri.split("/")[-1]
    return BuildCtx(
        projectid=pd.projectid,
        zip_name=zip_name,
        dockerfile=dockerfile,
        project_zip_route=uri,
        version=version,
        docker_name=docker,
        spec=spec,
        execid=_id,
        registry=registry,
    )
