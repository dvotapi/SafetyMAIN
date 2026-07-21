from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session, sessionmaker

T = TypeVar("T")


def run_in_session(session_factory: sessionmaker[Session], operation: Callable[[Session], T]) -> T:
    session = session_factory()
    try:
        result = operation(session)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def read_in_session(session_factory: sessionmaker[Session], operation: Callable[[Session], T]) -> T:
    session = session_factory()
    try:
        return operation(session)
    finally:
        session.close()
