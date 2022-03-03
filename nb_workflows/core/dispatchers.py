from typing import Union

import docker
from nb_workflows import client
from nb_workflows.conf import settings
from nb_workflows.core.core import nb_job_executor
from nb_workflows.core.entities import (ExecutionResult, HistoryResult,
                                             NBTask, ScheduleData)
from nb_workflows.core.models import WorkflowModel
from sqlalchemy import select


def local_exec(jobid) -> Union[ExecutionResult, None]:
    """Because rq-scheduler has some limitations
    and could be abandoned in the future, this abstraction was created
    where the idea is to use the scheduler only to enqueue through rq.

    Also, this way of schedule allows dinamically changes to the workflow
    task because the params are got from the database.
    """
    nb_client = client.from_file("workflows.toml")
    try:
        rsp = nb_client.get_workflow(jobid)
        if rsp and rsp.enabled:
            exec_res = nb_job_executor(rsp.task)
            nb_client.register_history(exec_res, rsp.task)

            return exec_res
        elif not rsp.task:
            nb_client.rq_cancel_job(jobid)
        else:
            print(f"{jobid} not enabled")
    except KeyError:
        print("Invalid credentials")
    except TypeError:
        print("Somenthing went wrong")
    return None


def docker_exec(jobid):
    docker_client = docker.from_env()
    nb_client = client.from_settings()
    try:
        rsp = nb_client.get_workflow(jobid)
        if rsp and rsp.enabled:
            docker_client.containers.run("nuxion/nb_workflows",
                                         f"nb workflows exec -J {jobid}")
        elif not rsp.task:
            nb_client.rq_cancel_job(jobid)
        else:
            print(f"{jobid} not enabled")
    except KeyError:
        print("Invalid credentials")
    except TypeError:
        print("Somenthing went wrong")
    return None
