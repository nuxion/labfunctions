from typing import Union

from nb_workflows import client
from nb_workflows.conf.client_settings import settings
from nb_workflows.core.entities import ExecutionResult, NBTask, ScheduleData
from nb_workflows.core.notebooks import nb_job_executor
from nb_workflows.utils import set_logger


def local_exec(jobid) -> Union[ExecutionResult, None]:
    """Because rq-scheduler has some limitations
    and could be abandoned in the future, this abstraction was created
    where the idea is to use the scheduler only to enqueue through rq.

    Also, this way of schedule allows dinamically changes to the workflow
    task because the params are got from the database.
    """
    logger = set_logger("local_exec", level=settings.LOGLEVEL)
    logger.info(f"Runing {jobid}")
    nb_client = client.nb_from_file("workflows.yaml")
    try:
        rsp = nb_client.workflows_get(jobid)
        if rsp and rsp.enabled:
            task = NBTask(**rsp.job_detail)
            if task.schedule:
                task.schedule = ScheduleData(**rsp.job_detail["schedule"])
            exec_res = nb_job_executor(task)
            # nb_client.register_history(exec_res, task)
            return exec_res
        # elif not rsp:
        #    nb_client.rq_cancel_job(jobid)
        else:
            logger.warning(f"{jobid} not enabled")
    except KeyError:
        logger.error("Invalid credentials")
    except TypeError:
        logger.error("Something went wrong")
    return None


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
