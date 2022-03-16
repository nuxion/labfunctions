import time
from typing import Any, Dict, List

import invoke
import nanoid
from invoke import Responder

import docker

NAMESPACE = "nb"

SERVICES = {
    "postgres": "postgres:14-alpine",
    "redis": "redis:6-alpine",
}


ipam_pool = docker.types.IPAMPool(
    subnet="124.42.0.0/16",
    iprange="124.42.0.0/24",
    gateway="124.42.0.254",
    aux_addresses={"reserved1": "124.42.1.1"},
)
ipam = docker.types.IPAMConfig(pool_configs=[ipam_pool])


def envs2dict(envs):
    data = {e.split("=", maxsplit=1)[0]: e.split("=", maxsplit=1)[1] for e in envs}
    return data


def write_envsdict(fpath, envs_dict):

    with open(fpath, "w") as f:
        for k, v in envs_dict.items():
            f.write(f"{k}={v}\n")


class DockerRunner:

    CLIENT_DCK = "nuxion/nb_workflows-client"
    SERVER_DCK = "nuxion/nb_workflows"

    def __init__(
        self, client: docker.client.DockerClient, namespace=NAMESPACE, version="latest"
    ):
        self.client: docker.client.DockerClient = client
        self.ns = namespace
        self._network = None
        self.network_name = None
        self.services: Dict[str, Any] = {}
        self.version = version
        self.tag_client = f"{self.CLIENT_DCK}:{version}"
        self.tag_server = f"{self.SERVER_DCK}:{version}"

    def open_env_file(self, env_file) -> List[str]:
        with open(env_file, "r") as f:
            data = f.readlines()

        final = []
        for line in data:
            if not line.startswith("#"):
                striped = line.strip("\n").strip()
                if striped:
                    final.append(striped)
        return final

    @classmethod
    def from_env(cls):
        obj = cls(client=docker.from_env())
        return obj

    def create_network(self, name):
        self._network = self.client.networks.create(
            f"{self.ns}-{name}", driver="bridge", ipam=ipam, check_duplicate=True
        )
        self.network_name = f"{self.ns}-{name}"

    def run_service(self, name, ports=None, envs=None, command=None, detach=True):
        srv = SERVICES[name]
        c = self.client.containers.run(
            name,
            network=self.network_name,
            environment=envs,
            name=f"{self.ns}-{name}",
            detach=detach,
        )
        self.services[name] = c

        return c

    def run_on_server_sdk(self, cmd, ports=None, envs=None, autoremove=True):
        c = self.client.containers.run(
            self.tag_client,
            command=cmd,
            auto_remove=autoremove,
            detach=True,
            environment=envs,
            ports=ports,
            network=self.network_name,
        )
        return c

    def run_on_server(
        self, cmd, tty=False, daemon=False, env_file=".env.dev.docker", watchers=None
    ):
        if not daemon:
            _cmd, id_ = self.ephemeral_server(tty, env_file=env_file)
            _exec = f"{_cmd} {cmd}"
        else:
            _cmd, id_ = self.daemon_server(env_file=env_file)
            _exec = f"{_cmd} {cmd}"

        rsp = invoke.run(_exec, pty=tty, watchers=watchers, warn=True)
        return rsp, id_

    def ephemeral_server(self, tty=True, env_file=".env.dev.docker"):
        id = nanoid.generate(size=6)
        if tty:
            base = (
                f"docker run --rm  --name={self.ns}-{id} -ti -e NB_SERVER=True "
                f"--env-file={env_file} --network={self.network_name} nuxion/nb_workflows "
            )
        else:
            base = (
                f"docker run --rm -e NB_SERVER=True "
                f"--env-file={env_file} --network={self.network_name} {self.tag_server} "
            )

        return base, f"{self.ns}-{id}"

    def daemon_server(self, env_file=".env.dev.docker"):
        id = nanoid.generate(size=6)
        base = (
            f"docker run --name={self.ns}-{id} -ti -e NB_SERVER=True -d "
            f"--env-file={env_file} --network={self.network_name} {self.tag_server} "
        )

        return base, f"{self.ns}-{id}"

    def run_on_client(self, cmd, tty=True, env_file=".env.dev.docker", watchers=None):
        docker_str = self.ephemeral_client(tty, env_file=env_file)
        exec_ = f"{docker_str} {cmd}"
        # try:
        rsp = invoke.run(exec_, watchers=watchers, pty=tty, warn=True)
        # except invoke.exceptions.UnexpectedExit as e:
        return rsp

    def ephemeral_client(self, tty=True, env_file=".env.docker.dev"):
        id = nanoid.generate(size=6)
        base = (
            f"docker run --rm -ti --name {self.ns}-{id} "
            f"--env-file={env_file} --network={self.network_name} {self.tag_client} "
        )
        return base

    def rm_docker(self, id):
        print("stopping...")
        try:
            rsp = invoke.run(f"docker stop {id}")
            print("Stopped")
        except invoke.UnexpectedExit:
            print("Service isn't running")
        try:
            rsp = invoke.run(f"docker rm {id}")
            print("Removed")
        except invoke.UnexpectedExit:
            print("Service doesn't exist")

    def run_postgres(self):
        envs = self.open_env_file(".env.dev.docker")
        return self.run_service("postgres", envs=envs, ports={"5432/tcp": "5432"})

    def run_redis(self):
        envs = self.open_env_file(".env.dev.docker")
        return self.run_service("redis", envs=envs, ports={"6379/tcp": "6379"})

    def delete_network(self, name=None):
        for n in self.client.networks.list():
            if n.name == f"{self.ns}-{name}":
                n.remove()
                break

    def clean(self):
        # for key in self.services:
        #     try:
        #         self.services[key].stop()
        #         self.services[key].remove()
        #     except docker.errors.NotFound:
        #         pass

        for c in self.client.containers.list(all=True):
            if c.name.startswith(f"{self.ns}-") or c.name.startswith(f"{self.ns}_"):
                self.rm_docker(c.id)
                # try:
                #     c.stop()
                # except docker.errors.NotFound:
                #     pass
                # c.remove()
        # time.sleep(5)
        for net in self.client.networks.list():
            if net.name.startswith(self.ns):
                net.remove()

    def get_ip(self, service_name):
        srv = self.services[service_name]
        c = self.client.containers.get(srv.id)
        _network = c.attrs["NetworkSettings"]["Networks"][self.network_name]
        return _network["IPAddress"]
