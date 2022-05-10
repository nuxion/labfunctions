import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.postgresql.base import PGInspector

# from sqlalchemy.dialects.postgresql import ARRAY
# from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from labfunctions.db.common import Base


def drop_everything(engine):
    """(On a live db) drops all foreign key constraints before dropping all tables.
    Workaround for SQLAlchemy not doing DROP ## CASCADE for drop_all()
    (https://github.com/pallets/flask-sqlalchemy/issues/722)
    """
    from sqlalchemy.engine.reflection import Inspector
    from sqlalchemy.schema import (
        DropConstraint,
        DropTable,
        ForeignKeyConstraint,
        MetaData,
        Table,
    )

    con = engine.connect()
    trans = con.begin()
    # inspector = Inspector.from_engine(engine)
    inspector = inspect(engine)

    # We need to re-create a minimal metadata with only the required things to
    # successfully emit drop constraints and tables commands for postgres (based
    # on the actual schema of the running instance)
    meta = MetaData()
    tables = []
    all_fkeys = []

    for table_name in inspector.get_table_names():
        fkeys = []

        for fkey in inspector.get_foreign_keys(table_name):
            if not fkey["name"]:
                continue

            fkeys.append(ForeignKeyConstraint((), (), name=fkey["name"]))

        tables.append(Table(table_name, meta, *fkeys))
        all_fkeys.extend(fkeys)

    for fkey in all_fkeys:
        con.execute(DropConstraint(fkey))

    for table in tables:
        con.execute(DropTable(table))

    trans.commit()


class SQL:
    def __init__(self, sqluri: str, pool_size=20, max_overflow=0, inspector=False):
        """
        :param sqluri: 'postgresql://postgres:secret@localhost:5432/twitter'
        """
        self._uri = sqluri
        if "sqlite" in sqluri.split("://", maxsplit=1)[0]:
            self.engine = create_engine(sqluri)
        else:
            self.engine = create_engine(
                sqluri, pool_size=pool_size, max_overflow=max_overflow
            )

        if inspector:
            self.inspector: PGInspector = inspect(self.engine)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

    def create_all(self):
        Sess = self.scoped_session()
        with Sess() as session:
            with session.begin():
                Base.metadata.create_all(self.engine)

    def drop_all(self):
        # Sess = self.scoped_session()
        # with Sess() as session:
        #    with session.begin():
        #        Base.metadata.drop_all(self.engine)
        drop_everything(self.engine)

    def list_tables(self):
        return self.inspector.get_tables_names()

    def sessionmaker(self, autoflush=True):
        """Session could be used as context manager
        Autocommit will be deprecated in SQLAlchemy 2.0
        Session.begin() method may be used to explicitly start transactions

        :param autoflush: When True, all query operations will issue a Session.
        flush() call to this Session before proceeding. Flush
        """

        session = sessionmaker(bind=self.engine, autoflush=autoflush, future=True)
        return session

    def scoped_session(self, autoflush=True) -> Session:
        """Scoped session return a Session object that could be used
        with a context manager

        https://docs.sqlalchemy.org/en/14/orm/session_basics.html#opening-and-closing-a-session

        """
        SSession = scoped_session(sessionmaker(autoflush=autoflush, bind=self.engine))

        return SSession
