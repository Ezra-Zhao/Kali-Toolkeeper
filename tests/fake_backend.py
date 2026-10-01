"""Shared fake backend for unit tests (mocks apt/dpkg entirely)."""
from __future__ import annotations

from toolkeeper.backend import PackageBackend
from toolkeeper.models import Package


class FakeBackend(PackageBackend):
    """In-memory backend: {name: (installed_version, candidate_version)}."""

    def __init__(self, data: dict[str, tuple[str | None, str | None]]):
        self.data = data

    def list_installed(self) -> list[Package]:
        return [
            Package(name=n, installed_version=v[0], candidate_version=v[1])
            for n, v in sorted(self.data.items())
            if v[0] is not None
        ]

    def candidate_version(self, name: str) -> str | None:
        entry = self.data.get(name)
        return entry[1] if entry else None

    def probe_binary(self, binary: str, timeout: int = 10) -> tuple[str, str]:
        return "ok", f"fake {binary}"
