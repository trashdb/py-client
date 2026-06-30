from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class TrashDBOptions:
    api_key: str
    base_url: str = "https://api.trashdb.dev/api/v1"
    max_retries: int = 3
    initial_backoff_ms: int = 500
    http_client: Optional[Callable[..., object]] = None


@dataclass
class CreateContainerParams:
    engine: str
    ttl_minutes: int = 5
    name: Optional[str] = None


@dataclass
class ContainerResponse:
    id: str
    engine: str
    port: int
    connection_string: str
    created_at: str
    ttl_minutes: int
    name: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class EngineInfo:
    id: str
    name: str
    max_ttl_minutes: int


@dataclass
class ContainerLogs:
    logs: str


ErrorInfo = dict  # {"code": int, "message": str}
