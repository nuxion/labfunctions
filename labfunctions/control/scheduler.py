from typing import Optional

from libq.connections import create_pool
from libq.jobs import Job
from libq.queue import Queue
from redis.asyncio import ConnectionPool

from labfunctions import conf, defaults, types
from labfunctions.executors import ExecID
from labfunctions.managers import runtimes_mg
from labfunctions.notebooks import create_notebook_ctx
from labfunctions.runtimes.context import create_build_ctx


class SchedulerExec:
    """
    It manages the logic to enqueue and dispatch jobs.
    The SchedulerExecutor belongs to the server side, it connects the webserver with
    the workers in the control plane.

    Because their main function wraps RQ and RQ-Scheduler some variables names could be
    confusing. When we talk about jobs we talk about the task executed by RQ or RQ-Scheduler.

    :param redis: A Redis instance
    :param qname: configured by default from settings, it MUST BE consistent between the different control plane components.
    """

    tasks = {
        "notebook": "labfunctions.control.tasks.notebook_dispatcher",
        "build": "labfunctions.control.tasks.build_dispatcher",
    }

    def __init__(
        self,
        conn: ConnectionPool = None,
        *,
        control_queue=defaults.CONTROL_QUEUE,
        build_queue=defaults.BUILD_QUEUE,
        build_timeout="1h",
        settings: types.ServerSettings = None,
    ):
        self.conn = conn or create_pool()

        self.control_q = Queue(control_queue, conn=self.conn)
        self.build_q = Queue(build_queue, conn=self.conn)
        self.settings: types.ServerSettings = settings or conf.load_server()
        self._build_ts = build_timeout
        # on_success=rq_job_ok, on_failure=rq_job_error)
        # self.scheduler = Scheduler(queue=self.Q, connection=self.redis)

    async def enqueue_notebook(
        self, session, *, projectid: str, task: types.NBTask
    ) -> types.ExecutionNBTask:

        execid = str(ExecID())
        runtime = None
        if task.runtime:
            runtime = await runtimes_mg.get_runtime(
                session, projectid, task.runtime, task.version
            )

        nb_ctx = create_notebook_ctx(projectid, task, execid=execid, runtime=runtime)

        qname = f"{nb_ctx.cluster}.{nb_ctx.machine}"
        Q = Queue(qname, conn=self.conn)
        job = await Q.enqueue(
            self.tasks["notebook"],
            execid=execid,
            timeout=task.timeout,
            background=True,
            params={"data": nb_ctx.dict()},
        )

        return nb_ctx

    async def enqueue_build(
        self,
        session,
        *,
        projectid: str,
        runtime: types.RuntimeSpec,
        version: Optional[str] = None,
    ) -> types.runtimes.BuildCtx:
        ctx = create_build_ctx(
            projectid,
            runtime,
            version,
            project_store_class=self.settings.PROJECTS_STORE_CLASS_SYNC,
            project_store_bucket=self.settings.PROJECTS_STORE_BUCKET,
            registry=self.settings.DOCKER_REGISTRY,
        )
        job = await self.build_q.enqueue(
            self.tasks["build"],
            execid=ctx.execid,
            timeout=self._build_ts,
            params={"data": ctx.dict()},
            background=True,
        )

        return ctx
