from __future__ import annotations

from collections.abc import Iterator
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.dependencies import get_readiness_check, get_settings, get_uow, get_uow_factory
from backend.bootstrap.container import AppContainer, create_container
from backend.bootstrap.settings import AppSettings
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.repositories import (
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
)
from backend.core.infrastructure.persistence.in_memory import InMemoryKnowledgeObjectRepository


class FakeUnitOfWork:
    """Lightweight UoW for API dependency tests."""

    instances: list[FakeUnitOfWork] = []

    def __init__(self) -> None:
        self.entered = False
        self.exited = False
        self.commit_calls = 0
        self.rollback_calls = 0
        self.exit_exc_type: type[BaseException] | None = None
        FakeUnitOfWork.instances.append(self)

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        raise RuntimeError("Not implemented in fake UoW.")

    @property
    def relations(self) -> KnowledgeObjectRelationRepositoryContract:
        raise RuntimeError("Not implemented in fake UoW.")

    @property
    def users(self):
        raise RuntimeError("Not implemented in fake UoW.")

    @property
    def organizations(self):
        raise RuntimeError("Not implemented in fake UoW.")

    @property
    def memberships(self):
        raise RuntimeError("Not implemented in fake UoW.")

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def __enter__(self) -> Self:
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.exited = True
        self.exit_exc_type = exc_type
        return None


@pytest.fixture
def app_settings() -> AppSettings:
    return AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=None,
        cors_allowed_origins=(),
    )


@pytest.fixture
def app(app_settings: AppSettings) -> FastAPI:
    FakeUnitOfWork.instances.clear()
    return create_app(settings=app_settings)


@pytest.fixture
def client(app: FastAPI, app_settings: AppSettings) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_readiness_check] = lambda: (lambda: None)

    def _fake_uow() -> Iterator[UnitOfWorkContract]:
        with FakeUnitOfWork() as uow:
            yield uow

    app.dependency_overrides[get_uow] = _fake_uow

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def isolated_container(app_settings: AppSettings) -> AppContainer:
    return create_container(app_settings)


def make_request_id() -> str:
    return f"req-{uuid4()}"


@pytest.fixture
def knowledge_object_client(
    app: FastAPI,
    app_settings: AppSettings,
) -> Iterator[tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID]]:
    from backend.core.infrastructure.persistence.in_memory import (
        InMemoryKnowledgeObjectRelationRepository,
        InMemoryKnowledgeObjectRepository,
        InMemoryUnitOfWork,
    )

    knowledge_objects = InMemoryKnowledgeObjectRepository()
    relations = InMemoryKnowledgeObjectRelationRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=knowledge_objects,
            relations=relations,
        )

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_readiness_check] = lambda: (lambda: None)
    app.dependency_overrides[get_uow_factory] = lambda: uow_factory

    organization_id = uuid4()
    with TestClient(app) as client:
        yield client, knowledge_objects, organization_id

    app.dependency_overrides.clear()

