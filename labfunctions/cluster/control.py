import json
from typing import Dict, List, Union

from redis.asyncio import ConnectionPool

from labfunctions.hashes import generate_random
from labfunctions.utils import get_class, open_publickey, open_yaml

from . import deploy
from .base import ProviderSpec
from .types import (
    AgentRequest,
    BlockStorage,
    ClusterFileType,
    ClusterSpec,
    DeployAgentRequest,
    MachineInstance,
    MachineOrm,
    MachineRequest,
    SSHKey,
)


class ClustersFile:
    def __init__(self, from_file: str):
        self.data: ClusterFileType = ClusterFileType(**open_yaml(from_file))
        self._from_file = from_file

    @property
    def providers(self) -> Dict[str, str]:
        return self.data.providers

    @property
    def path(self):
        return self._from_file

    def get_cluster(self, name: str) -> ClusterSpec:
        return self.data.clusters[name]

    def machines_by_provider(self, provider: str) -> List[MachineOrm]:
        machines = []
        for k, m in self.data.machines.items():
            if m.provider == provider:
                machines.append(m)
        return machines

    def get_provider(self, name: str, *args, **kwargs) -> ProviderSpec:
        prov: ProviderSpec = get_class(self.providers[name])(*args, **kwargs)
        return prov

    def get_machine(self, name: str) -> MachineOrm:
        return self.data.machines[name]

    def get_volume(self, name: str) -> BlockStorage:
        return self.data.volumes[name]

    def list_machines(self) -> List[str]:
        return list(self.data.machines.keys())

    def list_clusters(self) -> List[str]:
        return list(self.data.clusters.keys())


class ClusterControl:

    MACHINE_ABC = "0123456789abcdefghijklmnopqrstuvwxyz"
    CLOUD_TAG = "labfunctions"
    MACHINE_KEY = "lab.mch::"
    MACHINES_LIST = "lab.machines::"
    CLUSTERS_LIST = "lab.clusters"
    # CLUSTER_KEY = "lab.clusters::"

    def __init__(
        self,
        cluster_file: str,
        *,
        ssh_user: str,
        ssh_key_public_path: str,
        conn: ConnectionPool,
    ):
        # self.spec = spec
        self.cluster = ClustersFile(cluster_file)
        self.ssh_key: SSHKey = self._get_ssh_key(ssh_user, ssh_key_public_path)
        self.pub_key = open_publickey(self.ssh_key.public_path)
        self.redis = conn

    def _get_ssh_key(self, user, public_path) -> SSHKey:

        ssh = SSHKey(
            user=user,
            public_path=public_path,
        )

        ssh.private_path = ssh.public_path.split(".pub")[0]
        return ssh

    def get_cluster(self, name: str) -> ClusterSpec:
        return self.cluster.get_cluster(name)

    def machines_list_key(self, cluster_name: str) -> str:
        return f"{self.MACHINES_LIST}{cluster_name}"

    def _create_machine_req(
        self, machine_name: str, cluster_name: str, alias=None
    ) -> MachineRequest:
        machine = self.cluster.get_machine(machine_name)
        id = alias or generate_random(size=6, alphabet=self.MACHINE_ABC)
        name = f"{machine.name}-{id}"
        type_ = machine.machine_type
        gpu = "no"
        if machine.gpu:
            gpu = "yes"

        volumes = [self.cluster.get_volume(vol) for vol in machine.volumes]

        labels = {"cluster": cluster_name, "gpu": gpu, "tags": [self.CLOUD_TAG]}
        req = MachineRequest(
            name=name,
            ssh_public_cert=self.pub_key,
            ssh_user=self.ssh_key.user,
            gpu=machine.gpu,
            provider=machine.provider,
            image=type_.image,
            volumes=volumes,
            size=type_.size,
            location=machine.location,
            network=type_.network,
            labels=labels,
        )
        return req

    def create_instance(
        self,
        cluster_name: str,
        alias=None,
    ) -> MachineInstance:
        cluster = self.get_cluster(cluster_name)
        req = self._create_machine_req(cluster.machine, cluster.name, alias=alias)
        provider = self.cluster.get_provider(req.provider)

        instance = provider.create_machine(req)

        return instance

    def destroy_instance(self, machine_name: str, *, cluster_name: str):
        print(f"=> Destroying machine: {machine_name} for cluster {cluster_name}")
        cluster = self.get_cluster(cluster_name)
        provider = self.cluster.get_provider(cluster.provider)
        provider.destroy_machine(machine_name)

    async def register_instance(self, machine: MachineInstance, cluster_name: str):
        """
        It's register the creation of a machine in two places:
        as a simple key/value and in a list by cluster
        """
        async with self.redis.pipeline() as pipe:
            machine_list_key = self.machines_list_key(cluster_name)
            pipe.set(f"{self.MACHINE_KEY}{machine.machine_name}", machine.json())
            pipe.sadd(self.CLUSTERS_LIST, cluster_name)
            pipe.sadd(machine_list_key, machine.machine_name)
            await pipe.execute()

    async def unregister_instance(self, machine_name: str, cluster_name: str):
        async with self.redis.pipeline() as pipe:
            machine_list_key = self.machines_list_key(cluster_name)
            pipe.delete(f"{self.MACHINE_KEY}{machine_name}")
            pipe.srem(machine_list_key, machine_name)
            await pipe.execute()

    async def list_instances(self, cluster_name) -> List[str]:
        machine_list_key = self.machines_list_key(cluster_name)
        names = await self.redis.sinter(machine_list_key)
        return list(names)

    async def get_instance(self, machine_name) -> Union[MachineInstance, None]:
        data = await self.redis.get(f"{self.MACHINE_KEY}{machine_name}")
        if data:
            return MachineInstance(**json.loads(data))
        return None
