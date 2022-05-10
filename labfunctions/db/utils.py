from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.sql.selectable import Select


@dataclass
class PageCalc:
    limit: int
    offset: int
    next_page: int


@dataclass
class Pagination:
    total: int
    limit: int
    page: int


async def get_total_async(session, Model):
    """Should be made in a context manager"""
    stmt = select(func.count(Model.id))
    _total = await session.execute(stmt)
    total = _total.scalar()

    return total


def get_total(session, Model):
    """Should be made in a context manager"""
    stmt = select(func.count(Model.id))
    _total = session.execute(stmt)
    total = _total.scalar()

    return total


def pagination(s: Select, p: Pagination):

    offset = p.limit * (p.page - 1)
    next_page = p.page + 1
    next_offset = p.limit * p.page
    if next_offset >= p.total:
        next_page = -1
    stmt = s.limit(p.limit).offset(offset)
    return stmt, next_page


def calculate_page(total, limit, page) -> PageCalc:
    offset = limit * (page - 1)
    next_page = page + 1
    next_offset = limit * page
    if next_offset >= total:
        next_page = -1
    return PageCalc(limit=limit, offset=offset, next_page=next_page)
