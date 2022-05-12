from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from labfunctions import defaults


class DockerGPUSpec(BaseModel):
    cuda: str = "11.6"
    cudnn: str = "8.4.0.27-1+cuda11.6"
    cudnn_major_version = "8"
    nvidia_gpg_key = defaults.NVIDIA_GPG_KEY
    nvidia_gpg_version = defaults.NVIDIA_GPG_VERSION


class DockerAppUser(BaseModel):
    uid: int = defaults.DOCKER_APP_UID
    gid: int = defaults.DOCKER_APP_UID


class DockerSpec(BaseModel):
    image: str
    maintainer: str
    build_packages: Optional[str] = None
    final_packages: Optional[str] = None
    user: DockerAppUser = DockerAppUser()
    base_template: str = "Dockerfile.default"
    requirements: str = "requirements.txt"
    gpu: Optional[DockerGPUSpec] = None
    extra: Optional[Dict[str, Any]] = None


class RuntimeSpec(BaseModel):
    name: str
    container: DockerSpec
    description: Optional[str] = None
    gpu_support: bool = False
    version: Optional[str] = None
    registry: Optional[str] = None


class RuntimeReq(BaseModel):
    runtime_name: str
    docker_name: str
    spec: RuntimeSpec
    project_id: str
    version: str
    registry: Optional[str]


class RuntimeData(BaseModel):
    """
    docker_name should be nbworkflows/[projectid]-[runtime_name]:[version]
    """

    runtimeid: str
    runtime_name: str
    docker_name: str
    spec: RuntimeSpec
    project_id: str
    version: str
    created_at: Optional[str] = None
    registry: Optional[str] = None
    id: Optional[int] = None


class ProjectBundleFile(BaseModel):
    runtime_name: str
    version: str
    filepath: str
    filename: str
    commit: Optional[str]
    stash: Optional[bool] = False
    current: Optional[bool] = False
    format_type: str = "zip"


class BuildCtx(BaseModel):
    """
    It's is in charg of bring all the information needed to build
    docker containers.

    It has two entries: projects_bp and cli

    :param projectid: is needed to register the runtime built
    :param spec: Spec of the runtime to built
    :param docker_name: name of the docker
    :param version: version of the runtime, used to tag the docker image
    :param dockerfile: Name of the Dockerfile, by default is: "Dockerfile.default"
    :param zip_name: zip name: CURRENT.zip
    :param download_zip: path to the zip file, this shouldn't include
    nor bucket nor url
    :param execid: random id to register this task
    :param project_store_class: which type of storage use to download the bundle
    :param project_store_bucket: bucket to find the bundle file.

    :param registry: registry to push the docker image built
    """

    projectid: str  # ok
    spec: RuntimeSpec
    docker_name: str
    version: str
    dockerfile: str
    zip_name: str
    download_zip: str
    execid: str
    project_store_class: str
    project_store_bucket: str
    registry: Optional[str] = None
