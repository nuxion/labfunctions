from datetime import datetime

import factory
from factory import SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from nb_workflows import utils
from nb_workflows.client.state import WorkflowsState
from nb_workflows.client.types import Credentials
from nb_workflows.hashes import generate_random
from nb_workflows.managers.users_mg import password_manager
from nb_workflows.models import HistoryModel, ProjectModel, UserModel, WorkflowModel
from nb_workflows.types import (
    ExecutionNBTask,
    ExecutionResult,
    HistoryRequest,
    HistoryResult,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowDataWeb,
)
from nb_workflows.types.docker import DockerBuildCtx, DockerfileImage
from nb_workflows.types.events import EventSSE
from nb_workflows.types.users import UserData
from nb_workflows.utils import run_sync


class ProjectDataFactory(factory.Factory):
    class Meta:
        model = ProjectData

    name = factory.Sequence(lambda n: "pd-name%d" % n)
    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    username = factory.Sequence(lambda n: "user%d" % n)
    owner = factory.Sequence(lambda n: "user%d" % n)
    description = factory.Faker("text", max_nb_chars=24)
    # projectid = factory.


class ProjectReqFactory(factory.Factory):
    class Meta:
        model = ProjectReq

    name = factory.Sequence(lambda n: "pd-name%d" % n)
    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    private_key = factory.Faker("text", max_nb_chars=16)
    description = factory.Faker("text", max_nb_chars=24)
    # projectid = factory.


class ScheduleDataFactory(factory.Factory):
    class Meta:
        model = ScheduleData

    class Params:
        cron_like = True

    start_in_min = 0
    repeat = 2
    interval = factory.LazyAttribute(lambda o: None if o.cron_like else "5")
    cron = factory.LazyAttribute(lambda o: "0 * * * * *" if o.cron_like else None)


class NBTaskFactory(factory.Factory):
    class Meta:
        model = NBTask

    wfid = factory.LazyAttribute(lambda n: generate_random(24))
    alias = factory.Sequence(lambda n: "nb-alias%d" % n)
    nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    params = {"TEST": True, "TIMEOUT": 5}


class UserFactory(factory.Factory):
    class Meta:
        model = UserData

    user_id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: "u-name%d" % n)
    is_superuser = False
    is_active = True
    scopes = ["tester"]
    projects = None


class ExecutionNBTaskFactory(factory.Factory):
    class Meta:
        model = ExecutionNBTask

    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    wfid = factory.LazyAttribute(lambda n: generate_random(10))
    execid = factory.LazyAttribute(lambda n: generate_random(10))
    nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    params = {"TEST": True, "TIMEOUT": 5}
    machine = factory.Sequence(lambda n: "machine%d" % n)
    docker_name = factory.Sequence(lambda n: "docker%d" % n)
    pm_input = factory.Sequence(lambda n: "docker%d" % n)
    pm_output = factory.Sequence(lambda n: "docker%d" % n)
    output_dir = factory.Sequence(lambda n: "docker%d" % n)
    output_name = "test"
    error_dir = factory.Sequence(lambda n: "docker%d" % n)
    today = factory.LazyAttribute(lambda n: utils.today_string(format_="day"))
    timeout = 5
    created_at = factory.LazyAttribute(lambda n: datetime.utcnow().isoformat())


class ExecutionResultFactory(factory.Factory):
    class Meta:
        model = ExecutionResult

    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    execid = factory.LazyAttribute(lambda n: generate_random(10))
    wfid = factory.LazyAttribute(lambda n: generate_random(10))
    name = factory.Sequence(lambda n: "nb-name%d" % n)
    params = {"TEST": True, "TIMEOUT": 5}
    input_ = factory.Sequence(lambda n: "docker%d" % n)
    output_name = factory.Sequence(lambda n: "docker%d" % n)
    output_dir = factory.Sequence(lambda n: "docker%d" % n)
    error_dir = factory.Sequence(lambda n: "docker%d" % n)
    error = False
    elapsed_secs = 5
    created_at = factory.LazyAttribute(lambda n: datetime.utcnow().isoformat())


class WorkflowDataWebFactory(factory.Factory):
    class Meta:
        model = WorkflowDataWeb

    # nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    alias = factory.Sequence(lambda n: "nb-alias%d" % n)
    nbtask = factory.LazyAttribute(lambda n: NBTaskFactory())
    wfid = factory.LazyAttribute(lambda n: generate_random(24))
    schedule = factory.LazyAttribute(lambda n: ScheduleDataFactory())


class WorkflowDataFactory(factory.Factory):
    class Meta:
        model = WorkflowData

    # nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    alias = factory.Sequence(lambda n: "nb-alias%d" % n)
    nbtask = factory.LazyAttribute(lambda n: NBTaskFactory())
    wfid = factory.LazyAttribute(lambda n: generate_random(24))
    schedule = factory.LazyAttribute(lambda n: ScheduleDataFactory())


class WorkflowsStateFactory(factory.Factory):
    class Meta:
        model = WorkflowsState

    project = factory.LazyAttribute(lambda n: ProjectDataFactory())
    workflows = factory.LazyAttribute(lambda n: WorkflowDataWebFactory())


class EventSSEFactory(factory.Factory):
    class Meta:
        model = EventSSE

    data = factory.Sequence(lambda n: "message-%d" % n)


class HistoryResultFactory(factory.Factory):
    class Meta:
        model = HistoryResult

    class Params:
        status_ok = True

    wfid = factory.LazyAttribute(lambda n: generate_random(24))
    status = factory.LazyAttribute(lambda o: 1 if o.status_ok else -1)
    result = factory.LazyAttribute(lambda n: ExecutionResultFactory())
    execid = factory.LazyAttribute(lambda n: generate_random(10))
    created_at = factory.LazyAttribute(lambda n: datetime.utcnow().isoformat())


class DockerfileImageFactory(factory.Factory):
    class Meta:
        model = DockerfileImage

    maintener = factory.Sequence(lambda n: "maintener-%d" % n)
    image = "python-3.7"


class DockerBuildCtxFactory(factory.Factory):
    class Meta:
        model = DockerBuildCtx

    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    project_zip_route = "/tmp/test.current.zip"
    zip_name = "test.current.zip"
    version = "current"
    docker_name = "nbworkflows/test"
    execid = factory.LazyAttribute(lambda n: generate_random(10))


def create_user_model(*args, **kwargs) -> UserModel:
    uf = UserFactory(*args, **kwargs)
    pm = password_manager()
    _pass = kwargs.get("password", "meolvide")
    key = pm.encrypt(_pass)
    user = UserModel(
        id=uf.user_id,
        username=uf.username,
        password=key,
        is_superuser=uf.is_superuser,
        is_active=uf.is_active,
        scopes="tester"
        # groups=uf.groups,
        # projects=uf.projects
    )
    return user


def create_project_model(user: UserModel, *args, **kwargs) -> ProjectModel:
    pd = ProjectDataFactory(*args, **kwargs)
    pm = ProjectModel(
        projectid=pd.projectid,
        name=pd.name,
        private_key=b"key",
        description=pd.description,
        repository=pd.repository,
        owner=user,
    )
    return pm


def create_workflow_model(project: ProjectModel, *args, **kwargs) -> WorkflowModel:
    wd = WorkflowDataWebFactory(*args, **kwargs)
    wm = WorkflowModel(
        wfid=wd.wfid,
        alias=wd.alias,
        # nb_name=wd.nb_name,
        nbtask=wd.nbtask.dict(),
        schedule=wd.schedule.dict(),
        project=project,
    )
    return wm


def token_generator(auth, user=None, *args, **kwargs):
    _user = user or create_user_model(*args, **kwargs)
    tkn = run_sync(auth.generate_access_token, UserData.from_model(_user))
    return tkn


def credentials_generator(auth, user=None, *args, **kwargs):
    _user = user or create_user_model(*args, **kwargs)
    obj = UserData.from_model(_user)
    tkn = run_sync(auth.generate_access_token, obj)
    return Credentials(access_token=tkn, refresh_token="12345")


def create_history_request() -> HistoryRequest:
    task = NBTaskFactory()
    result = ExecutionResultFactory()
    return HistoryRequest(task=task, result=result)
