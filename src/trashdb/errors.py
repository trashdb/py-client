from __future__ import annotations

from typing import Any


class TrashDBAPIError(Exception):
    status: int
    code: int

    def __init__(self, status: int, error: dict[str, Any]) -> None:
        self.status = status
        self.code = error.get("code", 0)
        message = error.get("message", "Unknown error")
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.status}] code={self.code}: {self.args[0]}"


RETRYABLE_STATUSES: set[int] = {502, 503, 504}
