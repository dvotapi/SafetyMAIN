from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.dependencies import get_uow, get_uow_factory
from backend.bootstrap.settings import AppSettings
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from tests.api.conftest import FakeUnitOfWork


def test_uow_dependency_lifecycle_without_autocommit(
    app_settings: AppSettings,
) -> None:
    FakeUnitOfWork.instances.clear()
    application = create_app(settings=app_settings)

    def fake_factory() -> FakeUnitOfWork:
        return FakeUnitOfWork()

    application.dependency_overrides[get_uow_factory] = lambda: fake_factory

    @application.get("/_test/uow")
    def use_uow(uow: UnitOfWorkContract = Depends(get_uow)) -> dict[str, bool]:
        assert isinstance(uow, FakeUnitOfWork)
        assert uow.entered is True
        return {"ok": True}

    with TestClient(application) as client:
        response = client.get("/_test/uow")

    assert response.status_code == 200
    assert len(FakeUnitOfWork.instances) == 1
    uow = FakeUnitOfWork.instances[0]
    assert uow.entered is True
    assert uow.exited is True
    assert uow.commit_calls == 0


def test_uow_dependency_exits_on_exception(app_settings: AppSettings) -> None:
    FakeUnitOfWork.instances.clear()
    application = create_app(settings=app_settings)

    def fake_factory() -> FakeUnitOfWork:
        return FakeUnitOfWork()

    application.dependency_overrides[get_uow_factory] = lambda: fake_factory

    @application.get("/_test/uow-error")
    def use_uow_error(uow: UnitOfWorkContract = Depends(get_uow)) -> dict[str, bool]:
        raise RuntimeError("boom")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/_test/uow-error")

    assert response.status_code == 500
    assert len(FakeUnitOfWork.instances) == 1
    uow = FakeUnitOfWork.instances[0]
    assert uow.entered is True
    assert uow.exited is True
    assert uow.exit_exc_type is RuntimeError
    assert uow.commit_calls == 0


def test_one_uow_instance_per_request(app_settings: AppSettings) -> None:
    FakeUnitOfWork.instances.clear()
    application = create_app(settings=app_settings)

    def fake_factory() -> FakeUnitOfWork:
        return FakeUnitOfWork()

    application.dependency_overrides[get_uow_factory] = lambda: fake_factory

    @application.get("/_test/uow-once")
    def use_uow_once(
        first: UnitOfWorkContract = Depends(get_uow),
        second: UnitOfWorkContract = Depends(get_uow),
    ) -> dict[str, bool]:
        assert first is second
        return {"ok": True}

    with TestClient(application) as client:
        first_response = client.get("/_test/uow-once")
        second_response = client.get("/_test/uow-once")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(FakeUnitOfWork.instances) == 2


def test_override_get_uow_directly(app_settings: AppSettings) -> None:
    FakeUnitOfWork.instances.clear()
    application = create_app(settings=app_settings)

    def override() -> Iterator[UnitOfWorkContract]:
        with FakeUnitOfWork() as uow:
            yield uow

    application.dependency_overrides[get_uow] = override

    @application.get("/_test/uow-override")
    def use_override(uow: UnitOfWorkContract = Depends(get_uow)) -> dict[str, int]:
        assert isinstance(uow, FakeUnitOfWork)
        return {"commits": uow.commit_calls}

    with TestClient(application) as client:
        response = client.get("/_test/uow-override")

    assert response.status_code == 200
    assert response.json() == {"commits": 0}
    assert FakeUnitOfWork.instances[0].commit_calls == 0
