"""Safety guard: dry-run by default, explicit --yes for real changes, audit log always.

This is the most important module in the project. A tool that shells out to
apt-get must never surprise its operator.
"""
from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PlannedChange:
    """A system change that is planned but not yet executed."""

    description: str
    argv: list[str]

    @property
    def command(self) -> str:
        return " ".join(shlex.quote(a) for a in self.argv)


class SafetyGuard:
    """Gatekeeper for every mutating operation.

    - allow_changes=False (default): print what WOULD run, change nothing.
    - allow_changes=True (user passed --yes): run it, and log everything.
    - Both paths append to the audit log, so dry-runs are reviewable too.
    """

    def __init__(self, *, allow_changes: bool, log_path: Path):
        self.allow_changes = allow_changes
        self.log_path = log_path

    def execute(self, change: PlannedChange) -> int:
        if not self.allow_changes:
            print(f"[DRY-RUN] would run: {change.command}")
            print(f"          ({change.description})")
            print("          Re-run with --yes to apply for real. Nothing was changed.")
            self._log(f"DRY-RUN skipped: {change.command}  # {change.description}")
            return 0
        self._log(f"EXECUTE: {change.command}  # {change.description}")
        print(f"[EXECUTE] {change.command}")
        proc = subprocess.run(change.argv, text=True)
        self._log(f"EXIT={proc.returncode}: {change.command}")
        return proc.returncode

    def _log(self, line: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {line}\n")
