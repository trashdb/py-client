from __future__ import annotations

import os
from typing import Generator

import pytest

from trashdb import (
    ContainerResponse,
    CreateContainerParams,
    EngineInfo,
    TrashDB,
    TrashDBAPIError,
    TrashDBOptions,
)


@pytest.fixture
def api_key() -> str:
    key = os.environ.get("TRASHDB_API_KEY")
    if not key:
        pytest.skip("TRASHDB_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture
def client(api_key: str) -> Generator[TrashDB, None, None]:
    db = TrashDB(TrashDBOptions(api_key=api_key))
    yield db
    # No explicit close needed — urllib has no persistent connection


class TestEngines:
    def test_list_engines(self, client: TrashDB) -> None:
        engines = client.get_engines()
        assert isinstance(engines, list)
        assert len(engines) > 0

        engine = engines[0]
        assert isinstance(engine, EngineInfo)
        assert engine.id
        assert engine.name
        assert engine.max_ttl_minutes > 0


class TestContainers:
    @pytest.fixture
    def container(self, client: TrashDB) -> Generator[ContainerResponse, None, None]:
        params = CreateContainerParams(engine="postgres", ttl_minutes=3)
        c = client.create_container(params)
        yield c
        client.destroy_container(c.id)

    def test_create_and_destroy(self, client: TrashDB) -> None:
        params = CreateContainerParams(engine="postgres", ttl_minutes=3)
        c = client.create_container(params)
        assert isinstance(c, ContainerResponse)
        assert c.id
        assert c.engine == "postgres"
        assert c.port > 0
        assert c.connection_string
        assert c.ttl_minutes == 3

        destroyed = client.destroy_container(c.id)
        assert destroyed is True

    def test_create_with_name(self, client: TrashDB) -> None:
        params = CreateContainerParams(
            engine="postgres", ttl_minutes=3, name="my-integration-test"
        )
        c = client.create_container(params)
        assert c.name == "my-integration-test"
        client.destroy_container(c.id)

    def test_get_running_containers(
        self, client: TrashDB, container: ContainerResponse
    ) -> None:
        containers = client.get_running_containers()
        ids = [c.id for c in containers]
        assert container.id in ids

    def test_destroy_nonexistent(self, client: TrashDB) -> None:
        result = client.destroy_container("nonexistent-id")
        assert result is False

    def test_unauthorized(self) -> None:
        bad_client = TrashDB(TrashDBOptions(api_key="bad-key"))
        with pytest.raises(TrashDBAPIError) as exc_info:
            bad_client.create_container(CreateContainerParams(engine="postgres"))
        assert exc_info.value.status == 401
        assert exc_info.value.code == 4001

    def test_unsupported_engine(self, client: TrashDB) -> None:
        with pytest.raises(TrashDBAPIError) as exc_info:
            client.create_container(CreateContainerParams(engine="nonexistent"))
        assert exc_info.value.code == 1001

    def test_container_logs(self, client: TrashDB) -> None:
        params = CreateContainerParams(engine="postgres", ttl_minutes=3)
        c = client.create_container(params)
        try:
            logs = client.get_container_logs(c.id)
            assert isinstance(logs, str)
        finally:
            client.destroy_container(c.id)
