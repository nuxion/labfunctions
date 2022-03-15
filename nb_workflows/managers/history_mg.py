from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select

from nb_workflows.models import HistoryModel
from nb_workflows.types import ExecutionResult, HistoryResult, NBTask


@dataclass
class HistoryLastResponse:
    rows: List[HistoryResult]


def select_history():

    stmt = select(HistoryModel).options(selectinload(HistoryModel.project))
    return stmt


async def get_last(
    session, projectid: str, jobid: str, limit=1
) -> Union[HistoryLastResponse, None]:
    stmt = (
        select(HistoryModel)
        .where(HistoryModel.jobid == jobid)
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
                jobid=jobid,
                execid=r.execid,
                status=r.status,
                result=r.result,
                created_at=r.created_at.isoformat(),
            )
        )
    return HistoryLastResponse(rows=rsp)


async def get_exec_data(session, projectid: str, execid: str):
    """WORKING"""
    stmt = (
        select_history()
        .where(HistoryModel.project_id == projectid)
        .where(HistoryModel.execid == execid)
    )


async def create(session, execution_result: ExecutionResult) -> HistoryModel:
    result_data = execution_result.dict()

    status = 0
    if execution_result.error:
        status = -1

    row = HistoryModel(
        jobid=execution_result.jobid,
        execid=execution_result.execid,
        project_id=execution_result.projectid,
        elapsed_secs=execution_result.elapsed_secs,
        nb_name=execution_result.name,
        result=result_data,
        status=status,
    )
    session.add(row)
    return row
