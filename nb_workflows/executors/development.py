from typing import Union

from nb_workflows import client
from nb_workflows.conf.client_settings import settings
from nb_workflows.notebooks import nb_job_executor
from nb_workflows.types import ExecutionResult, NBTask, ScheduleData
from nb_workflows.utils import set_logger


def local_dev_exec(jobid) -> Union[ExecutionResult, None]:
    """Without server interaction
    jobid will be searched in the workflows file
    """
    logger = set_logger("local_exec", level=settings.LOGLEVEL)
    logger.info(f"Runing {jobid}")
    # nb_client = client.nb_from_file("workflows.yaml")

    wf = client.NBClient.read("workflows.yaml")
    for w in wf.workflows:
        if w.jobid == jobid:
            exec_res = nb_job_executor(w)
            # nb_client.register_history(exec_res, task)
            return exec_res
    print(f"{jobid} not found in workflows.yaml")
    return None
