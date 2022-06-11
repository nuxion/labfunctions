from typing import Dict, List

from labfunctions.hashes import generate_random
from labfunctions.utils import get_class, open_publickey, open_yaml

from .base import ProviderSpec
from .types import (
    BlockStorage,
    ClusterFileType,
    MachineInstance,
    MachineOrm,
    MachineRequest,
    SSHKey,
)


class ClusterFile:
    def __init__(self, from_file: str):
        self.data: ClusterFileType = ClusterFileType(**open_yaml(from_file))
        self._from_file = from_file

    @property
    def providers(self) -> Dict[str, str]:
        return self.data.spec.providers

    @property
    def path(self):
        return self._from_file

    @property
    def cluster_name(self) -> str:
        return self.data.spec.name

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


class ClusterControl:

    MACHINE_ABC = "0123456789abcdefghijklmnopqrstuvwxyz"
    CLOUD_TAG = "labfunctions"

    def __init__(self, cluster_file: str, *, ssh_user: str, ssh_key_public_path: str):
        # self.spec = spec
        self.cluster = ClusterFile(cluster_file)
        self.ssh_key: SSHKey = self._get_ssh_key(ssh_user, ssh_key_public_path)
        self.pub_key = open_publickey(self.ssh_key.public_path)

    def _get_ssh_key(self, user, public_path) -> SSHKey:

        ssh = SSHKey(
            user=user,
            public_path=public_path,
        )

        ssh.private_path = ssh.public_path.split(".pub")[0]
        return ssh

    @property
    def cluster_name(self) -> str:
        return self.cluster.cluster_name

    def _create_machine_req(self, machine_name: str, alias=None) -> MachineRequest:
        machine = self.cluster.get_machine(machine_name)
        id = alias or generate_random(size=6, alphabet=self.MACHINE_ABC)
        name = f"{machine.name}-{id}"
        type_ = machine.machine_type
        gpu = "no"
        if machine.gpu:
            gpu = "yes"

        volumes = [self.cluster.get_volume(vol) for vol in machine.volumes]

        labels = {"cluster": self.cluster_name, "gpu": gpu, "tags": [self.CLOUD_TAG]}

        req = MachineRequest(
            name=name,
            ssh_public_cert=self.pub_key,
            ssh_user=self.ssh_key.user,
            gpu=machine.gpu,
            provider=machine.provider,
            image=type_.image,
            volumes=machine.volumes,
            size=type_.size,
            location=machine.location,
            network=type_.network,
            labels=labels,
        )
        return req

    def create_instance(
        self,
        machine_name: str,
        *,
        alias=None,
        do_deploy=True,
        use_public=False,
        deploy_local=False,
    ) -> MachineInstance:
        req = self._create_machine_req(machine_name, alias=alias)
        provider = self.cluster.get_provider(req.provider)

        print(f"=> Creating machine: {req.name}")
        instance = provider.create_machine(req)
        # ip = instance.private_ips[0]
        # if use_public:
        #     ip = instance.public_ips[0]
        # req = deploy.agent_from_settings(
        #     ip,
        #     instance.machine_id,
        #     self.name,
        #     self.settings,
        #     qnames=ctx.qnames,
        #     worker_procs=ctx.worker_procs,
        #     docker_version=ctx.docker_version,
        # )
        # if do_deploy and deploy_local:
        #     res = deploy.agent_local(req, self.settings.dict())
        #     print("=> ", res)
        # elif do_deploy:
        #     res = deploy.agent(req, self.settings.dict())
        #     print("=> ", res)
        # self.register.register_machine(instance)
        return instance

    def destroy_instance(self, machine_name: str, *, provider: str):
        # agent = self.register.get(agent_name)
        # if agent:
        #     self.register.kill_workers_from_agent(agent.name)
        #     machine = self.register.get_machine(agent.machine_id)
        #     self.register.unregister(agent)
        #     self.register.unregister_machine(agent.machine_id)
        # else:
        #     machine = agent_name

        # machine = self.cluster.get_machine(machine_name)
        _provider = self.cluster.get_provider(provider)
        _provider.destroy_machine(machine_name)
