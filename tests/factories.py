from datetime import datetime

import factory
from factory import SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from nb_workflows.models import HistoryModel, WorkflowModel


def history_factory(session):
    class HistoryFactory(SQLAlchemyModelFactory):
        class Meta:
            model = HistoryModel
            sqlalchemy_session_persistence = "commit"
            sqlalchemy_session = session

        id = factory.Sequence(lambda n: n)
        jobid = factory.Faker("text", max_nb_chars=24)
        executionid = factory.Faker("text", max_nb_chars=24)
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
