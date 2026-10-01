"""Debian version comparison.

Implements the Debian version ordering: [epoch:]upstream[-debian_revision],
with the upstream/revision parts compared by the verrevcmp algorithm
(alternating non-digit / digit segments; '~' sorts before everything,
digits compare numerically).

This is a faithful implementation of the algorithm described in the
Debian Policy Manual (section 5.6.12). Edge cases in exotic version
strings should still be covered by tests before trusting it on a
production fleet — see tests/test_versioning.py.
"""
from __future__ import annotations


def _order(char: str) -> int:
    """Ordering key for a single non-digit character (or end-of-part)."""
    if char == "~":
        return -1
    if char == "":
        return 0
    if char.isalpha():
        return ord(char)
    return ord(char) + 256


def _verrevcmp(a: str, b: str) -> int:
    i = j = 0
    while i < len(a) or j < len(b):
        # 1. Compare the leading non-digit parts.
        while (i < len(a) and not a[i].isdigit()) or (j < len(b) and not b[j].isdigit()):
            ac = a[i] if (i < len(a) and not a[i].isdigit()) else ""
            bc = b[j] if (j < len(b) and not b[j].isdigit()) else ""
            oa, ob = _order(ac), _order(bc)
            if oa != ob:
                return -1 if oa < ob else 1
            if ac:
                i += 1
            if bc:
                j += 1
        # 2. Skip leading zeros, then compare digit runs numerically.
        while i < len(a) and a[i] == "0":
            i += 1
        while j < len(b) and b[j] == "0":
            j += 1
        i0, j0 = i, j
        while i < len(a) and a[i].isdigit():
            i += 1
        while j < len(b) and b[j].isdigit():
            j += 1
        if (i - i0) != (j - j0):
            return -1 if (i - i0) < (j - j0) else 1
        if a[i0:i] != b[j0:j]:
            return -1 if a[i0:i] < b[j0:j] else 1
    return 0


def _split_epoch(version: str) -> tuple[int, str]:
    epoch_str, sep, rest = version.partition(":")
    if sep and epoch_str.isdigit():
        return int(epoch_str), rest
    return 0, version


def _split_revision(upstream: str) -> tuple[str, str]:
    # The Debian revision is separated by the LAST hyphen.
    if "-" in upstream:
        up, _, rev = upstream.rpartition("-")
        return up, rev
    return upstream, ""


def debian_compare(v1: str, v2: str) -> int:
    """Return -1 if v1 < v2, 0 if equal, 1 if v1 > v2 (Debian ordering)."""
    e1, rest1 = _split_epoch(v1)
    e2, rest2 = _split_epoch(v2)
    if e1 != e2:
        return -1 if e1 < e2 else 1
    up1, rev1 = _split_revision(rest1)
    up2, rev2 = _split_revision(rest2)
    c = _verrevcmp(up1, up2)
    if c:
        return c
    return _verrevcmp(rev1, rev2)
