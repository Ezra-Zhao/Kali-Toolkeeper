# Kali-Toolkeeper

**Keep your Kali security tools inventoried, up to date, and healthy — without the fear of breaking your box.**

Kali Linux ships hundreds of security tools, but keeping track of what's installed, what's outdated, and what's actually working is manual busywork. Toolkeeper is a small, safety-first Python utility that inventories your Kali tools, flags outdated versions, updates them on your terms, manages install profiles (top10, web, wireless, …), and health-checks every tool binary.

It is **not** an OS and **not** a Kali replacement — just one practical tool that does one job well.

> **Project status: scaffold v0.1 (honest edition).**
> What works today: full CLI (inventory / check / update / profiles / doctor), Debian version comparison, dry-run safety guard with logging, and a complete **demo mode with simulated package data** that runs on any machine (no Kali required).
> What's still TODO (marked in code): hardening the real `apt`/`dpkg` parsing against edge cases on a live Kali system, and expanding the tool catalog. Nothing here pretends to manage a real system yet — demo mode is clearly labeled `SIMULATED`.

---

## The problem

On a working Kali box:

1. `apt list --installed` gives you a flat wall of packages — no idea which are security tools vs. system libs.
2. Tools go stale silently; an outdated `sqlmap` or `nmap` misses checks you assume it runs.
3. Rebuilding a familiar setup (web-testing laptop, wireless rig) means re-typing the same 30 package names.
4. A tool can be "installed" but broken — nobody runs `tool --version` on all 300 of them.

Toolkeeper answers: *what do I have, what's stale, fix it safely, and prove it works.*

## Features

| Command | What it does |
|---|---|
| `inventory` | Lists installed security tools grouped by category (recon, web, wireless, forensics, exploitation, password, sniffing, …) |
| `check` | Compares installed vs. repository versions; lists outdated tools |
| `update` | Upgrades selected tools or `--all` outdated ones |
| `profiles` | Named tool bundles (`top10`, `web`, `wireless`, `forensics`, …) — install/remove a whole kit with one command |
| `doctor` | Runs `<tool> --version` on every installed tool and reports OK / FAIL / TIMEOUT / MISSING |

## Safety design (this is the point)

System package managers deserve respect. Toolkeeper is **dry-run by default**:

- Every mutating operation first prints the exact command it *would* run: `[DRY-RUN] would run: apt-get install -y --only-upgrade nmap`
- Real changes require an explicit `--yes` flag — there is no config file or env var that silently enables it
- Every planned **and** executed change is appended to a log (`~/.local/share/toolkeeper/toolkeeper.log`) with a UTC timestamp
- In demo mode (`--demo`), nothing can touch your system at all — all data is simulated and labeled `SIMULATED`

## Quickstart

```bash
# Demo mode — works on any machine, no Kali needed, nothing touches your system
python -m toolkeeper --demo inventory
python -m toolkeeper --demo check
python -m toolkeeper --demo update --all          # dry-run: prints the apt commands
python -m toolkeeper --demo --yes update nmap    # simulated apply, still labeled SIMULATED
python -m toolkeeper --demo profiles list
python -m toolkeeper --demo profiles show web
python -m toolkeeper --demo doctor

# Tests
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

On a real Kali system (after the TODOs are hardened):

```bash
python -m toolkeeper inventory        # what's installed, by category
python -m toolkeeper check            # what's outdated
python -m toolkeeper update --all     # dry-run first, review, then:
python -m toolkeeper --yes update --all
python -m toolkeeper profiles install wireless
python -m toolkeeper doctor
```

Sample `check` output (demo data):

```
[SIMULATED] Installed 13 security tools, 5 outdated:
  OUTDATED  nmap                  7.94+dfsg1-1  ->  7.95+dfsg1-1
  OUTDATED  metasploit-framework  6.3.31-0kali1 ->  6.4.5-0kali1
  CURRENT   sqlmap                1.8.3-1
  UNKNOWN   burpsuite             2024.8.2-0kali1 (no candidate in repo metadata)
```

## Architecture

```
toolkeeper/
├── cli.py          # argparse: inventory / check / update / profiles / doctor
├── backend.py      # PackageBackend ABC — AptBackend (real) vs SimulatedBackend (demo)
├── versioning.py   # Debian version comparison (epoch / upstream / revision)
├── catalog.py      # tool -> category map, binary names, install profiles
├── inventory.py    # grouping logic
├── check.py        # installed-vs-candidate comparison
├── update.py       # upgrade planning
├── profiles.py     # bundle install/remove planning
├── doctor.py       # `<tool> --version` health checks
└── safety.py       # SafetyGuard: dry-run default, --yes gate, audit log
```

The `PackageBackend` abstraction is the seam: everything above it (grouping, diffing, planning) is backend-agnostic and fully unit-tested with mocks; only the thin backend layer talks to `dpkg`/`apt`.

## Roadmap

- Harden `AptBackend` parsing on live Kali (dpkg-query / apt-cache policy edge cases) — TODOs in code
- Expand the tool catalog (currently ~40 curated tools; Kali ships 600+)
- `profiles diff` — show what's missing from a profile vs. installed
- JSON output mode for scripting (`--json`)
- Optional `unattended` mode with explicit signed config (still never silent by default)

## License

MIT — see [LICENSE](LICENSE).
