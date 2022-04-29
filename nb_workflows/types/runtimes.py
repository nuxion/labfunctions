from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class DockerSpec(BaseModel):
    image: str
    maintener: str
    build_packages: str
    final_packages: Optional[str] = None
    user: Optional[Dict[str, int]] = None
    base_template: str = "Dockerfile"
    requirements: str = "requirements.txt"


class RuntimeSpec(BaseModel):
    name: str
    container: DockerSpec
    machine: Optional[str] = None
    gpu_support: bool = False
    version: Optional[str] = None


class RuntimeReq(BaseModel):
    runtime_name: str
    docker_name: str
    spec: RuntimeSpec
    project_id: str
    version: str


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
    id: Optional[int] = None


# class RuntimeOrm(BaseModel):
#     docker_name: str
#     runtime_name: str
#     spec: RuntimeSpec
#     version: str
#     project_id: str
#     created_at: datetime
#     id: Optional[int] = None
