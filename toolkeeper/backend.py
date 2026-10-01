"""Backend abstraction: the seam between planning logic and the real system.

All logic above this layer (inventory grouping, version diffing, profile
planning) is backend-agnostic and unit-tested with mocks. Only the thin
backend implementation touches dpkg/apt — or, in demo mode, simulated data.
"""
from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .models import Package
from .safety import PlannedChange, SafetyGuard


class PackageBackend(ABC):
    """Interface every backend must implement."""

    simulated: bool = False

    @abstractmethod
    def list_installed(self) -> list[Package]:
        """All installed packages known to this backend."""

    @abstractmethod
    def candidate_version(self, name: str) -> str | None:
        """Version the repo would install, or None if unknown."""

    @abstractmethod
    def probe_binary(self, binary: str, timeout: int = 10) -> tuple[str, str]:
        """Run `<binary> --version`. Returns (status, detail).
        status is one of: ok | fail | timeout | missing."""

    # -- planning (pure: build the command, don't run it) -------------------

    def plan_install(self, names: list[str]) -> PlannedChange:
        return PlannedChange(
            description=f"Install {len(names)} package(s): {', '.join(names)}",
            argv=["apt-get", "install", "-y", *names],
        )

    def plan_remove(self, names: list[str]) -> PlannedChange:
        return PlannedChange(
            description=f"Remove {len(names)} package(s): {', '.join(names)}",
            argv=["apt-get", "remove", "-y", *names],
        )

    def plan_upgrade(self, names: list[str]) -> PlannedChange:
        return PlannedChange(
            description=f"Upgrade {len(names)} package(s): {', '.join(names)}",
            argv=["apt-get", "install", "-y", "--only-upgrade", *names],
        )

    # -- execution -----------------------------------------------------------

    def execute(self, change: PlannedChange, guard: SafetyGuard) -> int:
        """Run a planned change through the safety guard (real backend)."""
        return guard.execute(change)


class AptBackend(PackageBackend):
    """Real backend: talks to dpkg/apt on a Kali (or any Debian) system.

    TODO(ezra): harden on a live Kali box —
      - dpkg-query format string edge cases (multi-arch suffixes like :amd64,
        packages in weird states like "config-files")
      - apt-cache policy output when a package has no candidate or multiple
        pinning sources; parse robustly instead of first-match
      - warn loudly when not running as root before planning anything
    """

    def list_installed(self) -> list[Package]:
        out = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Status}\n"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        packages = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue  # TODO(ezra): log unexpected lines instead of skipping silently
            name, version, status = parts
            if status.strip() == "install ok installed":
                packages.append(Package(name=name, installed_version=version))
        return packages

    def candidate_version(self, name: str) -> str | None:
        try:
            out = subprocess.run(
                ["apt-cache", "policy", name],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except subprocess.CalledProcessError:
            return None
        for line in out.splitlines():
            stripped = line.strip()
            if stripped.startswith("Candidate:"):
                candidate = stripped.split(":", 1)[1].strip()
                return None if candidate == "(none)" else candidate
        return None

    def probe_binary(self, binary: str, timeout: int = 10) -> tuple[str, str]:
        try:
            proc = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            return "missing", f"binary '{binary}' not found on PATH"
        except subprocess.TimeoutExpired:
            return "timeout", f"'{binary} --version' timed out after {timeout}s"
        if proc.returncode == 0:
            first_line = (proc.stdout or proc.stderr).splitlines()
            detail = first_line[0].strip() if first_line else "(no output)"
            return "ok", detail
        return "fail", f"exit code {proc.returncode}"


class SimulatedBackend(PackageBackend):
    """Demo backend: in-memory package data, clearly labeled SIMULATED.

    Even with --yes, NOTHING touches the real system: applies only mutate
    the in-memory copy and every message is stamped [SIMULATED].
    """

    simulated = True

    def __init__(self, data_path: str | Path):
        with open(data_path, encoding="utf-8") as f:
            self._data = json.load(f)
        self._installed: dict[str, dict] = {
            p["name"]: dict(p)
            for p in self._data["packages"]
            if p.get("installed") is not None
        }
        self._all: dict[str, dict] = {p["name"]: dict(p) for p in self._data["packages"]}

    def list_installed(self) -> list[Package]:
        return [
            Package(
                name=name,
                installed_version=entry["installed"],
                candidate_version=entry.get("candidate"),
                binary=entry.get("binary"),
            )
            for name, entry in sorted(self._installed.items())
        ]

    def candidate_version(self, name: str) -> str | None:
        entry = self._all.get(name)
        return entry.get("candidate") if entry else None

    def probe_binary(self, binary: str, timeout: int = 10) -> tuple[str, str]:
        for entry in self._all.values():
            if entry.get("binary") == binary and entry.get("installed"):
                status = entry.get("doctor", "ok")
                details = {
                    "ok": f"SIMULATED: {binary} --version succeeded",
                    "fail": f"SIMULATED: {binary} --version exited non-zero",
                    "timeout": f"SIMULATED: {binary} --version timed out",
                    "missing": f"SIMULATED: binary '{binary}' not found",
                }
                return status, details.get(status, status)
        return "missing", f"SIMULATED: binary '{binary}' not found"

    def execute(self, change: PlannedChange, guard: SafetyGuard) -> int:
        if not guard.allow_changes:
            return guard.execute(change)  # dry-run path: prints, changes nothing
        # Simulated apply: mutate in-memory state only, never the real system.
        print(f"[SIMULATED] applied: {change.description}")
        print("           (demo mode — your system was not touched)")
        guard._log(f"SIMULATED apply: {change.command}  # {change.description}")
        argv = change.argv
        if "--only-upgrade" in argv:
            for name in argv[argv.index("--only-upgrade") + 1:]:
                entry = self._installed.get(name)
                if entry and entry.get("candidate"):
                    entry["installed"] = entry["candidate"]
        elif argv[1:3] == ["install", "-y"]:
            for name in argv[3:]:
                entry = self._all.get(name)
                if entry:
                    installed_entry = dict(entry)
                    installed_entry["installed"] = entry.get("candidate") or "unknown"
                    self._installed[name] = installed_entry
        elif argv[1:3] == ["remove", "-y"]:
            for name in argv[3:]:
                self._installed.pop(name, None)
        return 0
