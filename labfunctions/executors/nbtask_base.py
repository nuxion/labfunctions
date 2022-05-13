import json
import logging
import os
import shutil
import time
import warnings
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from labfunctions import defaults
from labfunctions.client.diskclient import DiskClient
from labfunctions.client.nbclient import NBClient
from labfunctions.commands import DockerCommand, DockerRunResult
from labfunctions.types import ExecutionNBTask, ExecutionResult, NBTask
from labfunctions.types.runtimes import RuntimeData
from labfunctions.utils import get_version, today_string

from .execid import ExecID

warnings.filterwarnings("ignore", category=DeprecationWarning)


def _prepare_runtime(runtime: Optional[RuntimeData] = None) -> str:
    if not runtime:
        version = get_version()
        _runtime = f"{defaults.DOCKERFILE_IMAGE}:{version}"
    else:
        _runtime = f"{runtime.docker_name}:{runtime.version}"
        if runtime.registry:
            _runtime = f"{runtime.registry}/{runtime}"
    return _runtime


def _simple_retry(func, params, max_retries=3, wait_time=5):
    status = False
    tries = 0
    while status is not True and tries < 3:
        status = func(*params)
        tries += 1
        time.sleep(3)
    return status


class NBTaskExecBase:

    WFID_TMP = "tmp"

    def __init__(self, client: Union[NBClient, DiskClient]):
        self.client = client
        self.logger = logging.getLogger("nbworkf.server")

    @property
    def projectid(self) -> str:
        return self.client.projectid

    def _dummy_wfid(self):
        wfid = ExecID(size=defaults.WFID_LEN - len(self.WFID_TMP))
        return f"{self.WFID_TMP}{wfid}"

    def run(self, ctx: ExecutionNBTask) -> ExecutionResult:
        raise NotImplementedError()

    def register(self, result: ExecutionResult):
        self.client.history_register(result)
        if result.output_name:
            try:
                self.client.history_nb_output(result)
            except FileNotFoundError:
                print(f"WARNING: file not found for {result.execid}")

    def notificate(self, ctx: ExecutionNBTask, result: ExecutionResult):
        raise NotImplementedError()


class NBTaskDocker(NBTaskExecBase):
    cmd = "lab exec local"

    def build_env(self, data: Dict[str, Any]) -> Dict[str, Any]:
        priv_key = self.client.projects_private_key(data["projectid"])
        if not priv_key:
            raise IndexError(f"No priv key found for {data['projectid']}")

        env = {
            defaults.PRIVKEY_VAR_NAME: priv_key,
            defaults.EXECUTIONTASK_VAR: json.dumps(data),
            defaults.SERVICE_URL_ENV: self.client._addr,
            defaults.BASE_PATH_ENV: "/app",
        }
        return env

    def run(self, ctx: ExecutionNBTask) -> ExecutionResult:
        _started = time.time()
        env = self.build_env(ctx.dict())
        agent_token = self.client.projects_agent_token(projectid=ctx.projectid)
        env.update(
            {
                "LF_AGENT_TOKEN": agent_token.creds.access_token,
                "LF_AGENT_REFRESH_TOKEN": agent_token.creds.refresh_token,
            }
        )
        cmd = DockerCommand()
        result = cmd.run(
            self.cmd, ctx.runtime, timeout=ctx.timeout, env_data=env, require_gpu=ctx
        )
        error = False
        if result.status != 0:
            error = True

        elapsed = round(time.time() - _started)
        return ExecutionResult(
            projectid=ctx.projectid,
            name=ctx.nb_name,
            execid=ctx.execid,
            wfid=ctx.wfid,
            cluster=ctx.cluster,
            machine=ctx.machine,
            runtime=ctx.runtime,
            params=ctx.params,
            input_=ctx.pm_input,
            elapsed_secs=elapsed,
            output_dir=ctx.output_dir,
            output_name=ctx.output_name,
            error_dir=ctx.error_dir,
            error=error,
            error_msg=result.msg,
            created_at=ctx.created_at,
        )

    def notificate(self, ctx: ExecutionNBTask, result: ExecutionResult):
        pass


class NBTaskLocal(NBTaskExecBase):
    def run(self, ctx: ExecutionNBTask) -> ExecutionResult:
        import papermill as pm

        _started = time.time()
        _error = False
        _error_msg = None
        Path(ctx.output_dir).mkdir(parents=True, exist_ok=True)
        print(f"Current dir: {Path.cwd()}")
        print(f"Input: {ctx.pm_input}")
        try:
            pm.execute_notebook(ctx.pm_input, ctx.pm_output, parameters=ctx.params)
        except pm.exceptions.PapermillExecutionError as e:
            self.logger.error(f"jobdid:{ctx.wfid} execid:{ctx.execid} failed {e}")
            _error = True
            _error_msg = str(e)
            self._error_handler(ctx)

        elapsed = time.time() - _started
        return ExecutionResult(
            projectid=ctx.projectid,
            name=ctx.nb_name,
            wfid=ctx.wfid,
            execid=ctx.execid,
            cluster=ctx.cluster,
            machine=ctx.machine,
            runtime=ctx.runtime,
            params=ctx.params,
            input_=ctx.pm_input,
            output_dir=ctx.output_dir,
            output_name=ctx.output_name,
            error_dir=ctx.error_dir,
            error=_error,
            error_msg=_error_msg,
            elapsed_secs=round(elapsed, 2),
            created_at=ctx.created_at,
        )

    def notificate(self, ctx: ExecutionNBTask, result: ExecutionResult):
        pass

    def _error_handler(self, etask: ExecutionNBTask):
        error_output = f"{etask.error_dir}/{etask.output_name}"
        Path(etask.error_dir).mkdir(parents=True, exist_ok=True)
        shutil.move(etask.pm_output, error_output)
