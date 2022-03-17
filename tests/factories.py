from datetime import datetime

import factory
from factory import SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from nb_workflows import utils
from nb_workflows.auth.models import GroupModel, UserModel
from nb_workflows.auth.types import GroupData, UserData
from nb_workflows.auth.users import password_manager
from nb_workflows.hashes import generate_random
from nb_workflows.models import HistoryModel, ProjectModel, WorkflowModel
from nb_workflows.types import (
    ExecutionNBTask,
    NBTask,
    ProjectData,
    ScheduleData,
    SeqPipe,
    WorkflowDataWeb,
)
from nb_workflows.types.core import SeqPipeSpec
from nb_workflows.utils import run_sync


class ProjectDataFactory(factory.Factory):
    class Meta:
        model = ProjectData

    name = factory.Sequence(lambda n: "pd-name%d" % n)
    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    username = factory.Sequence(lambda n: "user%d" % n)
    description = "test"
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


class SeqPipeSpecFactory(factory.Factory):
    class Meta:
        model = SeqPipeSpec

    workflows = factory.LazyAttribute(lambda n: [generate_random(5) for x in range(5)])
    shared_volumes = ["data/", "models/"]


class SeqPipeFactory(factory.Factory):
    class Meta:
        model = SeqPipe

    spec = factory.LazyAttribute(lambda n: SeqPipeSpecFactory())
    alias = factory.Sequence(lambda n: "alias-%d" % n)


class GroupFactory(factory.Factory):
    class Meta:
        model = GroupData

    name = factory.Sequence(lambda n: "g-name%d" % n)


class UserFactory(factory.Factory):
    class Meta:
        model = UserData

    user_id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: "u-name%d" % n)
    is_superuser = False
    is_active = True
    groups = None
    projects = None


class WorkflowDataWebFactory(factory.Factory):
    class Meta:
        model = WorkflowDataWeb

    nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    alias = factory.Faker("text", max_nb_chars=24)
    nbtask = factory.LazyAttribute(lambda n: NBTaskFactory())
    wfid = factory.Faker("text", max_nb_chars=24)
    schedule = factory.LazyAttribute(lambda n: ScheduleDataFactory())


def create_user_model(*args, **kwargs) -> UserModel:
    uf = UserFactory(*args, **kwargs)
    pm = password_manager()
    _pass = kwargs.get("password", "meolvide")
    key = pm.encrypt(_pass)
    user = UserModel(
        username=uf.username,
        password=key,
        is_superuser=uf.is_superuser,
        is_active=uf.is_active,
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
        user=user,
    )
    return pm


def create_workflow_model(project: ProjectModel, *args, **kwargs) -> WorkflowModel:
    wd = WorkflowDataWebFactory(*args, **kwargs)
    wm = WorkflowModel(
        wfid=wd.wfid,
        alias=wd.alias,
        nb_name=wd.nb_name,
        nbtask=wd.nbtask.dict(),
        schedule=wd.schedule.dict(),
        project=project,
    )
    return wm


def token_generator(auth, user=None, *args, **kwargs):
    _user = user or create_user_model(*args, **kwargs)
    tkn = run_sync(auth.generate_access_token, _user)
    return tkn
