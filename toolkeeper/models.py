"""Core data model: a package as the backend sees it."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    """A system package relevant to Toolkeeper.

    installed_version is None  -> not installed on this system.
    candidate_version is None  -> no repo metadata known (unknown, not "current").
    """

    name: str
    installed_version: str | None
    candidate_version: str | None = None
    binary: str | None = None

    @property
    def installed(self) -> bool:
        return self.installed_version is not None
