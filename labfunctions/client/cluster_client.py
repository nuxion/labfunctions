from typing import Any, Dict, Generator, List, Optional, Union

from labfunctions import cluster, defaults, errors, secrets, types

from .base import BaseClient


class ClusterClient(BaseClient):
    """A client that manage cluster operations"""

    def cluster_get_specs(self) -> List[cluster.types.ClusterSpec]:

        rsp = self._http.get("/clusters/get-clusters-spec")

        if rsp.status_code != 200:
            raise errors.ClusterAPIError(f"Error getting cluster spec. {rsp.text}")

        return [cluster.types.ClusterSpec(**r) for r in rsp.json()]

    def cluster_create_instance(self, req: cluster.CreateRequest) -> str:
        rsp = self._http.post("/clusters", json=req.dict())
        if rsp.status_code != 202:
            raise errors.ClusterAPIError(f"Error creating cluster. {rsp.text}")

        return rsp.json()["jobid"]

    def cluster_deploy_agent(
        self, cluster_name: str, *, machine: str, req: cluster.DeployAgentRequest
    ) -> str:

        rsp = self._http.post(
            f"/clusters/{cluster_name}/{machine}/_agent", json=req.dict()
        )
        if rsp.status_code != 202:
            raise errors.ClusterAPIError(f"Error sending deploy agent task. {rsp.text}")

        return rsp.json()["jobid"]

    def cluster_destroy_instance(self, cluster_name: str, *, machine: str) -> str:
        rsp = self._http.delete(f"/clusters/{cluster_name}/{machine}")
        if rsp.status_code != 202 and rsp.status_code != 200:
            raise errors.ClusterAPIError(f"Error destroying instance. {rsp.text}")

        return rsp.json()["jobid"]

    def cluster_list_instances(self, cluster_name: str) -> List[str]:
        rsp = self._http.get(f"/clusters/{cluster_name}")
        if rsp.status_code != 200:
            raise errors.ClusterAPIError(f"Error listing instances. {rsp.text}")

        return rsp.json()
