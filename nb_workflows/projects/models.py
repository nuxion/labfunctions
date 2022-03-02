# pylint: disable=too-few-public-methods
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_serializer import SerializerMixin

from nb_workflows.db.common import Base


class ProjectModel(Base, SerializerMixin):
    """
    Register each execution of a workflow.

    :param jobid: Is the workflow jobid
    :param taskid: is random id generated for each execution of the workflow
    :param name: the filename of the notebook executed
    :param result: is the result of the task. TaskResult
    :param elapsed_secs: Time in seconds from the start of the task to the end.
    :param status: -1 fail, 0 ok.
    """

    __tablename__ = "nb_project"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String(128))
    folder = Column(String(24))  # should be execution id
    created_at = Column(DateTime(), default=datetime.utcnow(), nullable=False)

