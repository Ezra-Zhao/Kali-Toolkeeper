"""update: plan (and, with --yes, apply) upgrades for outdated tools."""
from __future__ import annotations

from dataclasses import replace

from .backend import PackageBackend
from .check import run_check
from .safety import PlannedChange, SafetyGuard


def plan_updates(
    backend: PackageBackend,
    names: list[str] | None = None,
    update_all: bool = False,
) -> PlannedChange | None:
    """Build the upgrade plan. Returns None when there is nothing to do."""
    outdated = {r.package: r for r in run_check(backend) if r.status == "outdated"}
    if names:
        unknown = [n for n in names if n not in {r.package for r in run_check(backend)}]
        if unknown:
            print(f"Not installed (nothing to update): {', '.join(unknown)}")
        targets = [n for n in names if n in outdated]
        not_outdated = [n for n in names if n not in outdated and n not in unknown]
        for n in not_outdated:
            print(f"Already current (skipped): {n}")
    elif update_all:
        targets = sorted(outdated)
    else:
        raise ValueError("update needs package names or --all")

    if not targets:
        print("Nothing to update.")
        return None

    detail = ", ".join(f"{n} {outdated[n].installed}->{outdated[n].candidate}" for n in targets)
    change = backend.plan_upgrade(targets)
    return replace(change, description=f"Upgrade {len(targets)} outdated tool(s): {detail}")


def run_update(
    backend: PackageBackend,
    guard: SafetyGuard,
    names: list[str] | None = None,
    update_all: bool = False,
) -> int:
    change = plan_updates(backend, names=names, update_all=update_all)
    if change is None:
        return 0
    return backend.execute(change, guard)
