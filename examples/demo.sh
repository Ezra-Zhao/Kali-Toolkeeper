#!/usr/bin/env bash
# Demo walkthrough — runs entirely on simulated data, safe on any machine.
set -e
cd "$(dirname "$0")/.."

echo "=== 1. inventory ==="
python3 -m toolkeeper --demo inventory
echo
echo "=== 2. check ==="
python3 -m toolkeeper --demo check
echo
echo "=== 3. update --all (dry-run) ==="
python3 -m toolkeeper --demo update --all
echo
echo "=== 4. update --all with --yes (simulated apply) ==="
python3 -m toolkeeper --demo --yes update --all
echo
echo "=== 5. profiles ==="
python3 -m toolkeeper --demo profiles list
python3 -m toolkeeper --demo profiles show wireless
echo
echo "=== 6. doctor ==="
python3 -m toolkeeper --demo doctor
