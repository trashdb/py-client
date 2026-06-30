from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from .errors import RETRYABLE_STATUSES, TrashDBAPIError
from .types import (
    ContainerResponse,
    CreateContainerParams,
    EngineInfo,
    TrashDBOptions,
)


def _dict_to_container(data: dict[str, Any]) -> ContainerResponse:
    return ContainerResponse(
        id=data["id"],
        engine=data["engine"],
        port=data["port"],
        connection_string=data["connectionString"],
        created_at=data["createdAt"],
        ttl_minutes=data["ttlMinutes"],
        name=data.get("name"),
        expires_at=data.get("expiresAt"),
    )


def _dict_to_engine(data: dict[str, Any]) -> EngineInfo:
    return EngineInfo(
        id=data["id"],
        name=data["name"],
        max_ttl_minutes=data["maxTtlMinutes"],
    )


class TrashDB:
    def __init__(self, options: TrashDBOptions) -> None:
        self._api_key = options.api_key
        self._max_retries = max(0, options.max_retries)
        self._initial_backoff_ms = options.initial_backoff_ms
        self._base_url = options.base_url.rstrip("/")

    def create_container(self, params: CreateContainerParams) -> ContainerResponse:
        body = {
            "engine": params.engine,
            "ttlMinutes": params.ttl_minutes,
        }
        if params.name is not None:
            body["name"] = params.name

        data = self._request(
            f"{self._base_url}/containers",
            method="POST",
            headers={"Content-Type": "application/json", "x-api-key": self._api_key},
            body=json.dumps(body).encode("utf-8"),
        )
        return _dict_to_container(data)

    def get_running_containers(self) -> list[ContainerResponse]:
        data = self._request(
            f"{self._base_url}/containers",
            headers={"x-api-key": self._api_key},
        )
        return [_dict_to_container(c) for c in data]

    def destroy_container(self, container_id: str) -> bool:
        try:
            self._raw_request(
                f"{self._base_url}/containers/{container_id}",
                method="DELETE",
                headers={"x-api-key": self._api_key},
            )
            return True
        except TrashDBAPIError as exc:
            if exc.status == 404:
                return False
            raise

    def get_engines(self) -> list[EngineInfo]:
        data = self._request(f"{self._base_url}/engines")
        return [_dict_to_engine(e) for e in data]

    def get_container_logs(
        self,
        container_id: str,
        tail: int = 200,
        since_seconds: Optional[int] = None,
    ) -> str:
        url = f"{self._base_url}/containers/{container_id}/logs?tail={tail}"
        if since_seconds is not None:
            url += f"&sinceSeconds={since_seconds}"

        data = self._request(url, headers={"x-api-key": self._api_key})
        return data["logs"]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> Any:
        res = self._raw_request(url, method=method, headers=headers, body=body)
        content = res.read()
        if not content:
            return None
        return json.loads(content.decode("utf-8"))

    def _raw_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> Any:
        max_attempts = self._max_retries + 1

        for attempt in range(1, max_attempts + 1):
            req = urllib.request.Request(url, data=body, method=method)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)

            try:
                return urllib.request.urlopen(req, timeout=30)

            except urllib.error.HTTPError as exc:
                if attempt == max_attempts or exc.code not in RETRYABLE_STATUSES:
                    error_body = exc.read()
                    error_data: dict[str, Any] = {}
                    if error_body:
                        try:
                            error_data = json.loads(error_body.decode("utf-8"))
                        except (json.JSONDecodeError, ValueError):
                            pass
                    raise TrashDBAPIError(exc.code, error_data) from exc

                self._sleep(attempt)

            except urllib.error.URLError as exc:
                if attempt == max_attempts:
                    raise TrashDBAPIError(0, {"message": str(exc.reason)}) from exc
                self._sleep(attempt)

        raise TrashDBAPIError(0, {"message": "Unreachable"})

    def _sleep(self, attempt: int) -> None:
        delay_ms = self._initial_backoff_ms * (2 ** (attempt - 1))
        time.sleep(delay_ms / 1000)
