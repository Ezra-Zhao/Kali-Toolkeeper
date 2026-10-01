"""CLI: toolkeeper [--demo] [--yes] <inventory|check|update|profiles|doctor>."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .backend import AptBackend, PackageBackend, SimulatedBackend
from .check import print_check, run_check
from .doctor import print_doctor, run_doctor
from .inventory import print_inventory, run_inventory
from .profiles import run_profiles
from .safety import SafetyGuard
from .update import run_update

DATA_PATH = Path(__file__).parent / "data" / "simulated_packages.json"
DEFAULT_LOG = Path.home() / ".local" / "share" / "toolkeeper" / "toolkeeper.log"


def build_backend(demo: bool) -> PackageBackend:
    if demo:
        return SimulatedBackend(DATA_PATH)
    return AptBackend()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="toolkeeper",
        description="Inventory, update, and health-check Kali security tools — safely.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--demo", action="store_true",
                   help="Demo mode: simulated package data, nothing touches your system.")
    p.add_argument("--yes", action="store_true",
                   help="Allow real system changes. Without it, everything is a dry-run.")
    p.add_argument("--log-file", type=Path, default=DEFAULT_LOG,
                   help="Audit log path (default: %(default)s).")
    p.add_argument("--timeout", type=int, default=10,
                   help="Seconds to wait for `<tool> --version` in doctor (default: %(default)s).")

    sub = p.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory", help="List installed security tools by category.")
    inv.add_argument("--category", help="Only show one category (e.g. web, wireless).")

    chk = sub.add_parser("check", help="List tools whose repo version is newer than installed.")
    chk.add_argument("--category", help="Only check one category.")

    upd = sub.add_parser("update", help="Upgrade outdated tools (dry-run unless --yes).")
    upd.add_argument("packages", nargs="*", help="Specific tools to update.")
    upd.add_argument("--all", action="store_true", help="Update all outdated tools.")

    prof = sub.add_parser("profiles", help="Manage named tool bundles.")
    prof_sub = prof.add_subparsers(dest="profile_action", required=True)
    prof_sub.add_parser("list", help="List available profiles.")
    show = prof_sub.add_parser("show", help="Show a profile's tools and install state.")
    show.add_argument("name")
    install = prof_sub.add_parser("install", help="Install a profile's missing tools.")
    install.add_argument("name")
    remove = prof_sub.add_parser("remove", help="Remove a profile's installed tools.")
    remove.add_argument("name")

    doc = sub.add_parser("doctor", help="Health-check installed tools via --version.")
    doc.add_argument("--category", help="Only check one category.")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    backend = build_backend(args.demo)
    guard = SafetyGuard(allow_changes=args.yes, log_path=args.log_file)

    if backend.simulated:
        print("[SIMULATED] demo mode — package data is fake, your system will not be touched.\n")
    elif args.command in ("update",) or (args.command == "profiles" and args.profile_action in ("install", "remove")):
        if not args.yes:
            print("(dry-run: add --yes to apply for real)\n")

    if args.command == "inventory":
        print_inventory(run_inventory(backend, args.category), backend.simulated)
    elif args.command == "check":
        results = run_check(backend)
        if args.category:
            from .catalog import categorize
            results = [r for r in results if categorize(r.package) == args.category]
        print_check(results, backend.simulated)
    elif args.command == "update":
        return run_update(backend, guard, names=args.packages or None, update_all=args.all)
    elif args.command == "profiles":
        return run_profiles(backend, guard, args.profile_action, args.name if hasattr(args, "name") else None)
    elif args.command == "doctor":
        print_doctor(run_doctor(backend, args.category, timeout=args.timeout), backend.simulated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
