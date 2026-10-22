"""Source snapshots: capture what was read, so a judgement can be re-derived.

A method that cites sources must be able to prove *which bytes* it saw. A snapshot
records the payload, its SHA-256 and when it was captured, so an assessment can be
re-run against the exact document it was built from, and a reviewer can confirm the
source has not silently changed underneath it.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptonym.security import SecurityValidationError, validate_service_url

MAX_SNAPSHOT_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class Snapshot:
    """A captured source document with its provenance."""

    source: str
    sha256: str
    captured_at: str
    content: str

    @classmethod
    def capture(cls, source: str, content: str, captured_at: str | None = None) -> Snapshot:
        size = len(content.encode("utf-8"))
        if size > MAX_SNAPSHOT_BYTES:
            raise SecurityValidationError(
                f"snapshot of {size} bytes exceeds the {MAX_SNAPSHOT_BYTES // (1024 * 1024)} MiB limit"
            )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stamp = captured_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(source=source, sha256=digest, captured_at=stamp, content=content)

    def verify(self) -> bool:
        """True when the content still matches its recorded digest."""
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest() == self.sha256

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "sha256": self.sha256,
            "captured_at": self.captured_at,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Snapshot:
        return cls(
            source=data["source"],
            sha256=data["sha256"],
            captured_at=data["captured_at"],
            content=data["content"],
        )


def fetch(
    source: str, *, fetcher: Callable[[str], str] | None = None, allow_private: bool = False
) -> Snapshot:
    """Fetch a source over HTTP(S) and capture it.

    The endpoint is validated (SSRF-aware) before use. The request itself is delegated
    to ``fetcher`` so the core stays offline and testable.
    """
    endpoint = validate_service_url(source, allow_private=allow_private)
    payload = (fetcher or _default_fetcher)(endpoint)
    return Snapshot.capture(source, payload)


def write(path: str | Path, snapshot: Snapshot) -> None:
    Path(path).write_text(json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load(path: str | Path) -> Snapshot:
    return Snapshot.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _default_fetcher(url: str, timeout: int = 15) -> str:  # pragma: no cover - network only
    request = urllib.request.Request(url, headers={"User-Agent": "cryptonym"})  # noqa: S310
    response = urllib.request.urlopen(request, timeout=timeout)  # noqa: S310  # nosec B310
    with response:
        return response.read().decode("utf-8", "replace")
