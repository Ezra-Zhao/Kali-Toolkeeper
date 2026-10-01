"""doctor: run `<tool> --version` on every installed tool; report health."""
from __future__ import annotations

from dataclasses import dataclass

from .backend import PackageBackend
from .catalog import binary_for, categorize


@dataclass(frozen=True)
class DoctorResult:
    package: str
    binary: str
    status: str  # ok | fail | timeout | missing
    detail: str


def run_doctor(
    backend: PackageBackend,
    category: str | None = None,
    timeout: int = 10,
) -> list[DoctorResult]:
    results = []
    for pkg in backend.list_installed():
        if category and categorize(pkg.name) != category:
            continue
        binary = pkg.binary or binary_for(pkg.name)
        status, detail = backend.probe_binary(binary, timeout=timeout)
        results.append(DoctorResult(pkg.name, binary, status, detail))
    return sorted(results, key=lambda r: (r.status == "ok", r.package))


def print_doctor(results: list[DoctorResult], simulated: bool) -> None:
    tag = "[SIMULATED] " if simulated else ""
    bad = [r for r in results if r.status != "ok"]
    print(f"{tag}Health-checked {len(results)} tools: {len(results) - len(bad)} OK, {len(bad)} need attention\n")
    for r in results:
        icon = {"ok": "OK     ", "fail": "FAIL   ", "timeout": "TIMEOUT", "missing": "MISSING"}.get(r.status, r.status)
        print(f"  {icon}  {r.package:<24} {r.detail}")
    if bad:
        print("\nTip: try `update <tool>` for FAIL results, or reinstall MISSING ones via profiles.")
