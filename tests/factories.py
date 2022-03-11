from datetime import datetime

import factory
from factory import SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from nb_workflows import utils
from nb_workflows.hashes import generate_random
from nb_workflows.models import HistoryModel, WorkflowModel
from nb_workflows.types import ExecutionNBTask, NBTask, ProjectData, ScheduleData


def history_factory(session):
    class HistoryFactory(SQLAlchemyModelFactory):
        class Meta:
            model = HistoryModel
            sqlalchemy_session_persistence = "commit"
            sqlalchemy_session = session

        id = factory.Sequence(lambda n: n)
        jobid = factory.Faker("text", max_nb_chars=24)
        execid = factory.Faker("text", max_nb_chars=24)
        nb_name = factory.Faker("text", max_nb_chars=24)
        result = dict()
        # project_id = "Az"
        elapsed_secs = float(5)
        status = 0

    return HistoryFactory


def workflow_factory(session):
    class WorkflowFactory(SQLAlchemyModelFactory):
        class Meta:
            model = WorkflowModel
            sqlalchemy_session_persistence = "commit"
            sqlalchemy_session = session

        id = factory.Sequence(lambda n: n)
        jobid = factory.Faker("text", max_nb_chars=24)
        alias = factory.Faker("text", max_nb_chars=24)
        nb_name = factory.Faker("text", max_nb_chars=24)
        job_detail = {}
        # project_id = "Az"
        enabled = True

    return WorkflowFactory


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

    jobid = factory.LazyAttribute(lambda n: generate_random(24))
    nb_name = factory.Sequence(lambda n: "nb-name%d" % n)
    params = {"TEST": True, "TIMEOUT": 5}


class ExecutionNBTaskFactory(factory.Factory):
    class Meta:
        model = ExecutionNBTask

    projectid = factory.LazyAttribute(lambda n: generate_random(10))
    jobid = factory.LazyAttribute(lambda n: generate_random(10))
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
