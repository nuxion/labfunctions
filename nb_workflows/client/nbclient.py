import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Union

from nb_workflows import errors, secrets
from nb_workflows.types import (
    ExecutionResult,
    HistoryRequest,
    HistoryResult,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowsList,
)

from .history_client import HistoryClient
from .projects_client import ProjectsClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import get_private_key, store_credentials_disk, store_private_key
from .workflows_client import WorkflowsClient


class NBClient(WorkflowsClient, ProjectsClient, HistoryClient):
    """An staleless client without disk side effects"""

    pass
