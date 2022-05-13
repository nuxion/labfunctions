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

from labfunctions.db.common import Base

assoc_projects_users = Table(
    "lf_projects_users",
    Base.metadata,
    Column("project_id", ForeignKey("lf_project.projectid")),
    Column("user_id", ForeignKey("lf_user.id")),
)


@declarative_mixin
class ProjectRelationMixin:
    # pylint: disable=no-self-argument

    @declared_attr
    def project_id(cls):
        return Column(
            String(16),
            ForeignKey("lf_project.projectid", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def project(cls):
        return relationship("ProjectModel")


@declarative_mixin
class UserMixin:

    id = Column(BigInteger, primary_key=True)
    password = Column(BINARY, nullable=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    scopes = Column(String(), default="user", nullable=False)

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

    __tablename__ = "lf_history"
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

    __tablename__ = "lf_project"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    projectid = Column(String(16), index=True, unique=True, nullable=False)
    name = Column(String(128), unique=True, nullable=False)
    private_key = Column(BINARY, nullable=False)
    description = Column(String())
    repository = Column(String(2048), nullable=True)
    owner_id = Column(
        BigInteger,
        ForeignKey("lf_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner = relationship(
        "labfunctions.models.UserModel", foreign_keys="ProjectModel.owner_id"
    )
    # agent_id = Column(
    #     BigInteger,
    #     ForeignKey("lf_user.id", ondelete="SET NULL"),
    #     nullable=True,
    # )
    # agent = relationship(
    #     "labfunctions.models.UserModel", foreign_keys="ProjectModel.agent_id"
    # )
    users = relationship(
        "labfunctions.models.UserModel",
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


class UserModel(UserMixin, Base):
    __tablename__ = "lf_user"
    __mapper_args__ = {"eager_defaults": True}

    username = Column(String(), index=True, unique=True, nullable=False)
    email = Column(String(), index=True, nullable=True)
    is_agent = Column(Boolean(), index=True, nullable=False, default=False)
    projects = relationship(
        "ProjectModel", secondary=assoc_projects_users, back_populates="users"
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

    __tablename__ = "lf_workflow"
    __table_args__ = (
        UniqueConstraint("alias", "project_id", name="_lf_workflow__project_alias"),
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


class NotebookFile(Base, ProjectRelationMixin):
    """
    Notebook Register
    """

    __tablename__ = "lf_notebook_file"
    __table_args__ = (
        UniqueConstraint(
            "nb_name", "project_id", name="_lf_notebook_file__name_project"
        ),
    )
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    nb_name = Column(String(24), index=True)
    remote_path = Column(String(24), nullable=True)

    params = Column(String(), nullable=True)
    runtimeid = Column(String(), index=True, nullable=False)
    owner = relationship(
        "labfunctions.models.UserModel", foreign_keys="NotebookFile.owner_id"
    )
    owner_id = Column(
        BigInteger,
        ForeignKey("lf_user.id", ondelete="SET NULL"),
        nullable=False,
    )
    created_at = Column(DateTime(), server_default=functions.now(), nullable=False)


class RuntimeModel(Base, ProjectRelationMixin):
    """
    Runtimes Register
    runtimeid = [projectid]/[runtime_name]/[version]
    runtime_name = should be nbworkflows/[projectid]-[runtime_name]
    """

    __tablename__ = "lf_runtime"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(Integer, primary_key=True)
    runtimeid = Column(String(), unique=True, index=True, nullable=False)
    runtime_name = Column(String(), index=True, nullable=False)
    docker_name = Column(String(), nullable=False)
    spec = Column(JSON(), nullable=False)
    version = Column(String(), nullable=False)
    registry = Column(String(), nullable=True)

    created_at = Column(
        DateTime(), server_default=functions.now(), nullable=False, index=True
    )


class MachineModel(Base):

    __tablename__ = "lf_machine"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint("name", "provider", name="_lf_machine__name_provider"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True, index=True, nullable=False)
    location = Column(String(), unique=False, index=True, nullable=False)
    provider = Column(String(), nullable=False, index=True)
    desc = Column(String(), nullable=True)
    machine_type = Column(JSON(), nullable=False)
    gpu = Column(JSON(), nullable=True)
    volumes = Column(JSON(), nullable=True)

    created_at = Column(
        DateTime(), server_default=functions.now(), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(),
        server_default=functions.now(),
        nullable=False,
    )
