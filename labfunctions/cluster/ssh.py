from typing import List

import asyncssh
from asyncssh.process import SSHCompletedProcess


async def run_cmd(
    addr: str, cmd: str, keys: List[str], username="op", known_hosts=None, check=False
) -> SSHCompletedProcess:
    """
    A opinated wrapper around asyncssh
    :param addr: ip address to connect
    :param cmd: a simple string with the command to run
    :param keys: a List of keys names to be used without extension
    :param username: user to use for ssh connection
    :param known_hosts: validate server host, if None this check will ignored
    :param check: if true an a remote error happend it will raise an exceptions
    """

    async with asyncssh.connect(
        addr, username=username, client_keys=keys, known_hosts=known_hosts
    ) as conn:
        result = await conn.run(cmd, check=check)
    return result


async def scp_from_local(
    remote_addr: str,
    remote_dir: str,
    local_file: str,
    keys: List[str],
    username="op",
    known_hosts=None,
):
    """
    Copy a local file to remote server
    :param remote_addr: ip address to connect
    :param remote_dir: dir where files should be copied
    :param local_file: local file to be copied
    :param keys: a List of keys names to be used without extension
    :param username: user to use for ssh connection
    :param known_hosts: validate server host, if None this check will ignored
    """

    async with asyncssh.connect(
        remote_addr, username=username, client_keys=keys, known_hosts=known_hosts
    ) as conn:
        await asyncssh.scp(local_file, (conn, remote_dir))
