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
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table
from sqlalchemy_serializer import SerializerMixin

from nb_workflows.db.common import Base

association_table = Table(
    "auth_user_groups",
    Base.metadata,
    Column("user_id", ForeignKey("auth_user.id")),
    Column("group_id", ForeignKey("auth_group.id")),
)


class UserModel(Base, SerializerMixin):

    __tablename__ = "auth_user"
    __mapper_args__ = {"eager_defaults": True}
    serialize_rules = ("-password",)

    id = Column(BigInteger, primary_key=True)
    username = Column(String(), index=True, unique=True, nullable=False)
    password = Column(BYTEA, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    groups = relationship(
        "GroupModel", secondary=association_table, back_populates="users"
    )
    created_at = Column(DateTime(), default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime(), default=datetime.utcnow())


class GroupModel(Base, SerializerMixin):

    __tablename__ = "auth_group"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    name = Column(String(), index=True, unique=True, nullable=False)
    users = relationship(
        "UserModel", secondary=association_table, back_populates="groups"
    )
