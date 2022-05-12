from dataclasses import dataclass

import greenlet
from sqlalchemy import func, select
from sqlalchemy.sql.selectable import Select
from sqlalchemy.util._concurrency_py3k import _AsyncIoGreenlet
from sqlalchemy.util.concurrency import await_only


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


def running_in_greenlet():
    return isinstance(greenlet.getcurrent(), _AsyncIoGreenlet)


def sync_as_async(fn):
    """https://github.com/sqlalchemy/sqlalchemy/discussions/5923
    It runs a session from the sync world into async functions"""

    def go(*arg, **kw):
        if running_in_greenlet():
            return await_only(fn(*arg, **kw))
        else:
            # no greenlet, assume no event loop and blocking IO backend
            coro = fn(*arg, **kw)
            try:
                coro.send(None)
            except StopIteration as err:
                return err.value

    return go
