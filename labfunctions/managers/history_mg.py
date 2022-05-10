from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from labfunctions.models import HistoryModel
from labfunctions.types import (
    ExecutionResult,
    HistoryLastResponse,
    HistoryResult,
    NBTask,
)


def select_history():

    stmt = select(HistoryModel).options(selectinload(HistoryModel.project))
    return stmt


async def get_last(
    session, projectid: str, wfid: Optional[str] = None, limit=1
) -> Union[HistoryLastResponse, None]:
    if wfid:
        stmt = (
            select(HistoryModel)
            .where(HistoryModel.wfid == wfid)
            .where(HistoryModel.project_id == projectid)
            .order_by(HistoryModel.created_at.desc())
            .limit(limit)
        )
    else:
        stmt = (
            select(HistoryModel)
            .where(HistoryModel.project_id == projectid)
            .order_by(HistoryModel.created_at.desc())
            .limit(limit)
        )

    r = await session.execute(stmt)
    results = r.scalars()
    if not results:
        return None

    rsp = []
    for r in results:
        rsp.append(
            HistoryResult(
                wfid=r.wfid,
                execid=r.execid,
                status=r.status,
                result=r.result,
                created_at=r.created_at.isoformat(),
            )
        )
    return HistoryLastResponse(rows=rsp)


async def get_one(session, execid: str) -> Union[HistoryResult, None]:
    stmt = select(HistoryModel).where(HistoryModel.execid == execid).limit(1)
    r = await session.execute(stmt)
    model: Union[HistoryModel, None] = r.scalar_one_or_none()
    hr = None
    if model:
        hr = HistoryResult(
            wfid=model.wfid,
            execid=model.execid,
            status=model.status,
            result=model.result,
            created_at=model.created_at.isoformat(),
        )
    return hr


async def create(session, execution_result: ExecutionResult) -> HistoryModel:
    result_data = execution_result.dict()

    status = 0
    if execution_result.error:
        status = -1

    row = HistoryModel(
        wfid=execution_result.wfid,
        execid=execution_result.execid,
        project_id=execution_result.projectid,
        elapsed_secs=execution_result.elapsed_secs,
        nb_name=execution_result.name,
        result=result_data,
        status=status,
    )
    session.add(row)
    return row
