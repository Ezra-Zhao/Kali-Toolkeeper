"""inventory: group installed security tools by category."""
from __future__ import annotations

from .backend import PackageBackend
from .catalog import categorize
from .models import Package


def run_inventory(backend: PackageBackend, category: str | None = None) -> dict[str, list[Package]]:
    grouped: dict[str, list[Package]] = {}
    for pkg in backend.list_installed():
        cat = categorize(pkg.name)
        if category and cat != category:
            continue
        grouped.setdefault(cat, []).append(pkg)
    return {cat: sorted(pkgs, key=lambda p: p.name) for cat, pkgs in sorted(grouped.items())}


def print_inventory(grouped: dict[str, list[Package]], simulated: bool) -> None:
    tag = "[SIMULATED] " if simulated else ""
    total = sum(len(pkgs) for pkgs in grouped.values())
    print(f"{tag}Installed security tools: {total} across {len(grouped)} categories\n")
    for cat, pkgs in grouped.items():
        print(f"  [{cat}] ({len(pkgs)})")
        for pkg in pkgs:
            print(f"    {pkg.name:<24} {pkg.installed_version}")
    if not grouped:
        print("  (no catalogued security tools installed)")
