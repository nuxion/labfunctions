# pylint: disable=too-few-public-methods
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

# from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship
from sqlalchemy.schema import Table
from sqlalchemy.sql import functions
from sqlalchemy.types import BINARY, JSON
from sqlalchemy_serializer import SerializerMixin

from nb_workflows.db.common import Base

assoc_projects_users = Table(
    "nb_projects_users",
    Base.metadata,
    Column("project_id", ForeignKey("nb_project.projectid")),
    Column("user_id", ForeignKey("nb_auth_user.id")),
)


@declarative_mixin
class ProjectRelationMixin:
    # pylint: disable=no-self-argument

    @declared_attr
    def project_id(cls):
        return Column(
            String(16),
            ForeignKey("nb_project.projectid", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def project(cls):
        return relationship("ProjectModel")


class HistoryModel(Base, SerializerMixin, ProjectRelationMixin):
    """
    Register each execution of a workflow.

    :param wfid: Is the workflow wfid
    :param taskid: is random id generated for each execution of the workflow
    :param name: the filename of the notebook executed
    :param result: is the result of the task. TaskResult
    :param elapsed_secs: Time in seconds from the start of the task to the end.
    :param status: -1 fail, 0 ok.
    """

    __tablename__ = "nb_history"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    wfid = Column(String(24))
    execid = Column(String(24))  # should be execution id
    nb_name = Column(String(), nullable=False)
    result = Column(JSON, nullable=False)
    elapsed_secs = Column(Float(), nullable=False)
    status = Column(Integer, index=True)

    created_at = Column(
        DateTime(),
        server_default=functions.now(),
        index=True,
        nullable=False,
    )


class ProjectModel(Base, SerializerMixin):
    """
    Register each execution of a workflow.

    :param wfid: Is the workflow wfid
    :param taskid: is random id generated for each execution of the workflow
    :param name: the filename of the notebook executed
    :param result: is the result of the task. TaskResult
    :param elapsed_secs: Time in seconds from the start of the task to the end.
    :param status: -1 fail, 0 ok.
    """

    __tablename__ = "nb_project"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    projectid = Column(String(16), index=True, unique=True, nullable=False)
    name = Column(String(128), unique=True, nullable=False)
    private_key = Column(BINARY, nullable=False)
    description = Column(String())
    repository = Column(String(2048), nullable=True)
    owner_id = Column(
        BigInteger,
        ForeignKey("nb_auth_user.id", ondelete="SET NULL"),
        nullable=False,
    )
    owner = relationship(
        "nb_workflows.models.UserModel", foreign_keys="ProjectModel.owner_id"
    )
    agent_id = Column(
        BigInteger,
        ForeignKey("nb_auth_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent = relationship(
        "nb_workflows.models.UserModel", foreign_keys="ProjectModel.agent_id"
    )
    users = relationship(
        "nb_workflows.models.UserModel",
        secondary=assoc_projects_users,
        back_populates="projects",
    )
    created_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )


class WorkflowModel(Base, SerializerMixin, ProjectRelationMixin):
    """
    Configuration for each workflow.

    :param wfid: an unique identifier for this workflow
    :param alias: because the filename could be shared between different
    workflows, an alias was added to identify each instance, and is more
    friendly than wfid.
    :param name: name of the notebook file.
    :param description: A friendly description of the purpose of this workflow
    :param nbtask: details to execute a notebook with specific parameters.
    :param schedule: when should be executed.
    :param enabled: if the task should run or not.
    """

    __tablename__ = "nb_workflow"
    __table_args__ = (
        UniqueConstraint("alias", "project_id", name="_nb_workflow__project_alias"),
    )
    # needed for async support
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, primary_key=True)
    wfid = Column(String(24), index=True, unique=True)
    alias = Column(String(33), index=True, nullable=False)
    # nb_name = Column(String(), nullable=False)
    nbtask = Column(JSON(), nullable=False)
    schedule = Column(JSON(), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(), server_default=functions.now(), nullable=False)

    updated_at = Column(DateTime(), server_default=functions.now())


class RuntimeVersionModel(Base, ProjectRelationMixin):
    """
    Runtimes Register
    """

    __tablename__ = "nb_runtime"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, primary_key=True)
    docker_name = Column(String(), unique=True, index=True, nullable=False)
    version = Column(String(), nullable=False)

    created_at = Column(
        DateTime(), server_default=functions.now(), nullable=False, index=True
    )


class UserModel(Base):

    __tablename__ = "nb_auth_user"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    username = Column(String(), index=True, unique=True, nullable=False)
    password = Column(BINARY, nullable=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    scopes = Column(String(), default="user", nullable=False)

    projects = relationship(
        "ProjectModel", secondary=assoc_projects_users, back_populates="users"
    )
    created_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
