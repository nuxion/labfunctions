import time

from labfunctions.cluster import ssh
from labfunctions.cluster.base import ProviderSpec
from labfunctions.cluster.context import machine_from_settings
from labfunctions.types.cluster import DataFolder
from labfunctions.types.config import ServerSettings
from labfunctions.utils import run_sync


def snapshot_volume(provider: ProviderSpec, settings: ServerSettings):
    pass


def initialize_datafolder(
    provider: ProviderSpec, projectid: str, name: str, location: str
):
    pass


def create_snapshot(
    provider: ProviderSpec,
    settings,
    public=False,
    location=None,
    name="ext4-base-disk",
    size=2,
    filesystem="ext4",
):
    ctx = machine_from_settings("snapshooter", ["snapshot"], settings)
    ctx.node.location = location or ctx.node.location
    ctx.node.volumes[0].size = size
    instance = provider.create_machine(ctx.node)
    breakpoint()
    key = ctx.ssh_key.private_path
    vol = ctx.node.volumes[0]
    mount_cmd = (
        f"sudo mkdir -p {vol.mount} && "
        f"sudo mount /dev/disk/by-id/{vol.name}  {vol.mount} && "
        f"sudo mkdir -p {vol.mount} && "
        f"sudo chown {ctx.docker_uid}:{ctx.docker_gid} {vol.mount}"
    )
    ip = instance.private_ips[0]
    if public:
        ip = instance.public_ips[0]
    retry = 3
    while retry < 3:
        try:
            run_sync(ssh.run_cmd, ip, mount_cmd, keys=[key])
            retry = 4
        except ConnectionRefusedError:
            retry += 1
            time.sleep(5 + retry)

    _vol = [v for v in provider.driver.list_volumes() if v.name == vol.name][0]
    provider.driver.create_volume_snapshot(_vol, name)
    provider.destroy_machine(ctx.node.name)
    provider.driver.destroy_volume(_vol)


if __name__ == "__main__":
    from labfunctions.cluster.gcloud_provider import GCEProvider
    from labfunctions.conf.server_settings import settings

    g = GCEProvider()
    create_snapshot(g, settings, public=True)
