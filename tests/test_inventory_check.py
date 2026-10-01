"""Unit tests for inventory grouping and version checking (mocked backend)."""
from tests.fake_backend import FakeBackend
from toolkeeper.check import run_check
from toolkeeper.inventory import run_inventory


def _backend():
    return FakeBackend(
        {
            "nmap": ("7.94+dfsg1-1", "7.95+dfsg1-1"),   # outdated
            "sqlmap": ("1.8.3-1", "1.8.3-1"),           # current
            "burpsuite": ("2024.8.2-0kali1", None),      # unknown candidate
            "some-random-lib": ("1.0-1", "1.0-1"),       # not a catalogued tool
        }
    )


def test_inventory_groups_by_category():
    grouped = run_inventory(_backend())
    assert [p.name for p in grouped["recon"]] == ["nmap"]
    assert [p.name for p in grouped["web"]] == ["burpsuite", "sqlmap"]
    assert [p.name for p in grouped["other"]] == ["some-random-lib"]


def test_inventory_category_filter():
    grouped = run_inventory(_backend(), category="web")
    assert set(grouped) == {"web"}


def test_check_detects_outdated_current_unknown():
    results = {r.package: r.status for r in run_check(_backend())}
    assert results == {
        "nmap": "outdated",
        "sqlmap": "current",
        "burpsuite": "unknown",
        "some-random-lib": "current",
    }


def test_check_outdated_sorts_first():
    results = run_check(_backend())
    assert results[0].package == "nmap"
