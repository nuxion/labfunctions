from .cluster_client import ClusterClient
from .history_client import HistoryClient
from .projects_client import ProjectsClient
from .workflows_client import WorkflowsClient


class NBClient(WorkflowsClient, ProjectsClient, HistoryClient, ClusterClient):
    """An staleless client without disk side effects"""

    pass
