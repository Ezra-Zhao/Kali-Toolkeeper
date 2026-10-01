"""check: compare installed versions against repository candidates."""
from __future__ import annotations

from dataclasses import dataclass

from .backend import PackageBackend
from .versioning import debian_compare


@dataclass(frozen=True)
class CheckResult:
    package: str
    installed: str
    candidate: str | None
    status: str  # "outdated" | "current" | "unknown"


def run_check(backend: PackageBackend) -> list[CheckResult]:
    results = []
    for pkg in backend.list_installed():
        candidate = backend.candidate_version(pkg.name)
        if candidate is None:
            status = "unknown"
        elif debian_compare(pkg.installed_version or "", candidate) < 0:
            status = "outdated"
        else:
            status = "current"
        results.append(
            CheckResult(
                package=pkg.name,
                installed=pkg.installed_version or "?",
                candidate=candidate,
                status=status,
            )
        )
    return sorted(results, key=lambda r: (r.status != "outdated", r.package))


def print_check(results: list[CheckResult], simulated: bool) -> None:
    tag = "[SIMULATED] " if simulated else ""
    outdated = [r for r in results if r.status == "outdated"]
    print(f"{tag}Checked {len(results)} tools: {len(outdated)} outdated\n")
    for r in results:
        if r.status == "outdated":
            print(f"  OUTDATED  {r.package:<24} {r.installed}  ->  {r.candidate}")
        elif r.status == "unknown":
            print(f"  UNKNOWN   {r.package:<24} {r.installed}  (no candidate in repo metadata)")
        else:
            print(f"  CURRENT   {r.package:<24} {r.installed}")
    if outdated:
        print(f"\nRun `update --all` to plan the upgrades (dry-run by default).")
