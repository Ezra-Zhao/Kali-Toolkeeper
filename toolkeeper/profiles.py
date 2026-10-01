"""profiles: named tool bundles for one-command setup/teardown."""
from __future__ import annotations

from dataclasses import replace

from .backend import PackageBackend
from .catalog import get_profile, list_profiles
from .safety import PlannedChange, SafetyGuard


def plan_profile_install(backend: PackageBackend, name: str) -> PlannedChange | None:
    wanted = get_profile(name)
    if wanted is None:
        print(f"Unknown profile: {name}. Available: {', '.join(list_profiles())}")
        return None
    installed = {p.name for p in backend.list_installed()}
    missing = [p for p in wanted if p not in installed]
    if not missing:
        print(f"Profile '{name}': everything already installed.")
        return None
    change = backend.plan_install(missing)
    return replace(
        change,
        description=f"Install profile '{name}' ({len(missing)} new tools): {', '.join(missing)}",
    )


def plan_profile_remove(backend: PackageBackend, name: str) -> PlannedChange | None:
    wanted = get_profile(name)
    if wanted is None:
        print(f"Unknown profile: {name}. Available: {', '.join(list_profiles())}")
        return None
    installed = {p.name for p in backend.list_installed()}
    present = [p for p in wanted if p in installed]
    if not present:
        print(f"Profile '{name}': none of its tools are installed.")
        return None
    change = backend.plan_remove(present)
    return replace(
        change,
        description=f"Remove profile '{name}' ({len(present)} tools): {', '.join(present)}",
    )


def run_profiles(
    backend: PackageBackend,
    guard: SafetyGuard,
    action: str,
    name: str | None = None,
) -> int:
    if action == "list":
        for profile_name in list_profiles():
            pkgs = get_profile(profile_name) or []
            print(f"  {profile_name:<12} ({len(pkgs)} tools)")
        return 0
    if action == "show":
        pkgs = get_profile(name or "")
        if pkgs is None:
            print(f"Unknown profile: {name}. Available: {', '.join(list_profiles())}")
            return 1
        installed = {p.name for p in backend.list_installed()}
        for pkg in pkgs:
            mark = "[installed]" if pkg in installed else "[missing]  "
            print(f"  {mark} {pkg}")
        return 0
    if action == "install":
        change = plan_profile_install(backend, name or "")
        return backend.execute(change, guard) if change else 0
    if action == "remove":
        change = plan_profile_remove(backend, name or "")
        return backend.execute(change, guard) if change else 0
    raise ValueError(f"unknown profiles action: {action}")
