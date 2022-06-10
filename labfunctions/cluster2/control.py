from labfunctions import types

from .base import ProviderSpec
from .context import machine_from_settings
from .inventory import Inventory
from .types import ClusterSpec


class ClusterControl:
    def __init__(
        self,
        spec: ClusterSpec,
        *,
        cluster_name="default",
        inventory: Inventory,
        settings: types.ServerSettings,
    ):
        # self.spec = spec
        self.inventory = inventory
        self.spec = spec
        self.settings = settings
        self.cluster_name = cluster_name
        self.provider = self.get_provider()

    @property
    def cluster_name(self) -> str:
        return self.spec.name

    def get_provider(self) -> ProviderSpec:
        return self.inventory.get_provider(self.cluster_name)

    def create_instance(
        self,
        do_deploy=True,
        use_public=False,
        deploy_local=False,
    ) -> types.machine.MachineInstance:
        ctx = machine_from_settings(
            self.spec.machine,
            cluster=self.cluster_name,
            qnames=self.spec.qnames,
            network=self.spec.network,
            location=self.spec.location,
            settings=self.settings,
            inventory=self.inventory,
        )
        print(f"=> Creating machine: {ctx.machine.name}")
        instance = self.provider.create_machine(ctx.machine)
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

    def destroy_instance(self, machine: str):
        # agent = self.register.get(agent_name)
        # if agent:
        #     self.register.kill_workers_from_agent(agent.name)
        #     machine = self.register.get_machine(agent.machine_id)
        #     self.register.unregister(agent)
        #     self.register.unregister_machine(agent.machine_id)
        # else:
        #     machine = agent_name
        self.provider.destroy_machine(machine)
