from datetime import datetime
from typing import Union

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows.conf.defaults import PIPEID_LEN
from nb_workflows.hashes import generate_random
from nb_workflows.models import SeqPipeModel
from nb_workflows.types import SeqPipe


def _create_or_update(projectid, pipeid: str, pipe: SeqPipe):
    spec_dict = None
    if pipe.spec:
        spec_dict = pipe.spec.dict()

    enabled = pipe.enabled or True

    stmt = insert(SeqPipeModel.__table__).values(
        pipeid=pipeid,
        alias=pipe.alias,
        spec=spec_dict,
        project_id=projectid,
        enabled=enabled,
    )
    stmt = stmt.on_conflict_do_update(
        # constraint="crawlers_page_bucket_id_fkey",
        index_elements=["pipeid"],
        set_=dict(
            spec=spec_dict,
            alias=pipe.alias,
            enabled=enabled,
            updated_at=datetime.utcnow(),
        ),
    )

    return stmt


def generate_pipeid(size=PIPEID_LEN) -> str:
    id_ = generate_random(size)
    return id_


def select_seqpipe():
    stmt = select(SeqPipeModel).options(selectinload(SeqPipeModel.project))
    return stmt


async def get_one(session, projectid, pipeid) -> Union[SeqPipeModel, None]:
    stmt = (
        select_seqpipe()
        .where(SeqPipeModel.project_id == projectid)
        .where(SeqPipeModel.pipeid == pipeid)
    )
    result = await session.execute(stmt)

    row = result.scalar_one_or_none()
    if row:
        return row
    return None


async def create(
    session, projectid: str, pipe: SeqPipe, pipeid=None
) -> Union[str, None]:
    id_ = pipeid or generate_pipeid()
    stmt = _create_or_update(projectid, id_, pipe)
    try:
        res = await session.execute(stmt)
        return id_
    except IntegrityError:
        return None


async def delete_pipe(session, projectid, pipeid):
    stmt = (
        delete(SeqPipeModel)
        .where(SeqPipeModel.project_id == projectid)
        .where(SeqPipeModel.pipeid == pipeid)
    )
    await session.execute(stmt)
