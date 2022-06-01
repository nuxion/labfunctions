from typing import Optional, Union

from libq import JobStoreSpec, Queue, RedisJobStore, Scheduler, create_pool
from libq.errors import JobNotFound
from libq.jobs import Job
from redis.asyncio import ConnectionPool

from labfunctions import conf, defaults, types
from labfunctions.executors import ExecID
from labfunctions.managers import runtimes_mg, workflows_mg
from labfunctions.notebooks import create_notebook_ctx
from labfunctions.runtimes.context import create_build_ctx


async def create_task_ctx(
    session, projectid: str, task: types.NBTask, prefix=None
) -> types.ExecutionNBTask:
    execid = str(ExecID(prefix=prefix))
    runtime = None
    if task.runtime:
        runtime = await runtimes_mg.get_runtime(
            session, projectid, task.runtime, task.version
        )

    nb_ctx = create_notebook_ctx(projectid, task, execid=execid, runtime=runtime)
    return nb_ctx


class JobManager:
    """
    Manage periodic tasks like Workflows
    """

    tasks = {
        "workflow": "labfunctions.control.tasks.workflow_dispatcher",
    }

    def __init__(self, conn: ConnectionPool = None, *, store: JobStoreSpec = None):

        self.conn = conn or create_pool()
        self.store = store or RedisJobStore(self.conn)
        self.scheduler = Scheduler(self.store, conn=self.conn)

    async def register_workflow(
        self, session, *, projectid: str, wd: types.WorkflowDataWeb
    ):
        runtime = None
        task = wd.nbtask

        qname = f"{task.cluster}.{task.machine}"
        ctx = await create_task_ctx(session, projectid, task)
        ctx.wfid = wd.wfid

        await self.scheduler.create_job(
            self.tasks["workflow"],
            queue=qname,
            jobid=wd.wfid,
            params={"data": ctx.dict()},
            interval=wd.schedule.interval,
            cron=wd.schedule.cron,
            background=True,
            repeat=wd.schedule.repeat,
        )
        await self.enqueue_job(wd.wfid)

    async def unregister_workflow(self, wfid: str, remove_job=True):
        await self.scheduler.unregister_job(wfid)
        if remove_job:
            await self.scheduler.remove_job(wfid)

    async def enqueue_job(self, jobid: str):
        await self.scheduler.enqueue_job(jobid)


class SchedulerExec:
    """
    It manages the logic to enqueue and dispatch jobs.
    The SchedulerExecutor belongs to the server side, it connects the webserver with
    the workers in the control plane.

    Because their main function wraps RQ and RQ-Scheduler some variables names could be
    confusing. When we talk about jobs we talk about the task executed by RQ or RQ-Scheduler.

    :param redis: A Redis instance
    :param qname: configured by default from settings, it MUST BE consistent
    between the different control plane components.
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
        self,
        session,
        *,
        projectid: str,
        task: types.NBTask,
        prefix=None,
    ) -> types.ExecutionNBTask:

        nb_ctx = await create_task_ctx(session, projectid, task, prefix=prefix)

        qname = f"{nb_ctx.cluster}.{nb_ctx.machine}"
        Q = Queue(qname, conn=self.conn)
        job = await Q.enqueue(
            self.tasks["notebook"],
            execid=nb_ctx.execid,
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

    async def enqueue_workflow(
        self, session, *, projectid: str, wfid: str
    ) -> Union[types.ExecutionNBTask, None]:
        execid = str(ExecID())
        runtime = None
        wd: types.WorkflowDataWeb = await workflows_mg.get_by_wfid_prj(
            session, projectid, wfid
        )
        if wd and wd.enabled:
            ctx = await self.enqueue_notebook(
                session, projectid=projectid, task=wd.nbtask
            )
            return ctx
        return None

    async def _get_job(self, execid: str) -> Union[Job, None]:
        job = Job(execid, conn=self.conn)
        try:
            await job.fetch()
        except JobNotFound:
            return None
        return job

    async def get_task(self, execid: str) -> Union[types.TaskStatus, None]:
        job = await self._get_job(execid)
        if not job:
            return None

        return types.TaskStatus(
            execid=execid,
            status=job.status,
            queue=job._payload.queue,
            retries=job._payload.retries,
        )
