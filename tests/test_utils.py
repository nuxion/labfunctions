import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from nb_workflows import utils
from nb_workflows.errors import CommandExecutionException

tmp_dir = TemporaryDirectory()


def test_utils_flatten_list():

    original = [[1, 2, 3]]
    final = utils.flatten_list(original)
    assert len(final) == 3


def test_utils_secure_filename():
    name = utils.secure_filename("test~!\1q@#((**$file/\/.hack#@")
    assert name == "testqfile__.hack"


def test_utils_write_yaml():
    utils.write_yaml(f"{tmp_dir.name}/tmp.yaml", {"hello": "yaml"})
    with open(f"{tmp_dir.name}/tmp.yaml") as f:
        dat = yaml.safe_load(f.read())
    assert dat["hello"] == "yaml"


def test_utils_set_logger():
    l = utils.set_logger("test", level="INFO")
    assert l.level == logging.INFO


def test_utils_Singleton():
    class Mem(metaclass=utils.Singleton):
        pass

    m = Mem()
    m2 = Mem()

    assert hash(m) == hash(m2)


def test_utils_execute_cmd():
    rsp = utils.execute_cmd("ls -l")
    assert isinstance(rsp, str)


def test_utils_execute_cmd_err():
    with pytest.raises(CommandExecutionException):
        rsp = utils.execute_cmd("mkdir /root/test")


def test_utils_path_relative():

    ex = "test/path//relative///noise"
    norm = utils.path_relative(ex)
    assert norm == "test/path/relative/noise"


def test_utils_fullpath_from_client():
    from nb_workflows.conf import load_client

    s = load_client()
    fp = utils.fullpath("test")
    assert fp == f"{s.BASE_PATH}/test"


def test_utils_fullpath_from_server():
    from nb_workflows.conf import load_server

    s = load_server()
    fp = utils.fullpath("test//test")
    assert fp == f"{s.BASE_PATH}/test/test"


def test_utils_mkdir_p():
    utils.mkdir_p(f"{tmp_dir.name}/mkdir_p")
    res = Path(f"{tmp_dir.name}/mkdir_p").is_dir()
    Path(f"{tmp_dir.name}/mkdir_p").rmdir()
    assert res


def test_utils_run_sync():
    async def message_dummy(msg):
        return msg * 2

    rsp = utils.run_sync(message_dummy, "hello")

    assert rsp == "hello" * 2


@pytest.mark.asyncio
async def test_utils_run_async():
    def sync_function(msg):
        return msg * 2

    rsp = await utils.run_async(sync_function, "hello")
    assert rsp == "hello" * 2


def test_utils_get_version():

    ver = utils.get_version("__version__.py")
    py_dict = utils.open_toml("pyproject.toml")
    assert ver == py_dict["tool"]["poetry"]["version"]
