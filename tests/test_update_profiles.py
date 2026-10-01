"""Unit tests for update planning and profiles (mocked backend)."""
from dataclasses import replace

from tests.fake_backend import FakeBackend
from toolkeeper import catalog
from toolkeeper.profiles import plan_profile_install, plan_profile_remove
from toolkeeper.update import plan_updates


def _backend():
    return FakeBackend(
        {
            "nmap": ("7.94+dfsg1-1", "7.95+dfsg1-1"),
            "sqlmap": ("1.8.3-1", "1.8.3-1"),
        }
    )


def test_plan_updates_all_only_targets_outdated():
    change = plan_updates(_backend(), update_all=True)
    assert change is not None
    assert change.argv == ["apt-get", "install", "-y", "--only-upgrade", "nmap"]
    assert "7.94+dfsg1-1->7.95+dfsg1-1" in change.description


def test_plan_updates_named_skips_current(capsys):
    change = plan_updates(_backend(), names=["sqlmap"])
    assert change is None
    assert "Already current" in capsys.readouterr().out


def test_plan_updates_nothing_to_do(capsys):
    backend = FakeBackend({"sqlmap": ("1.8.3-1", "1.8.3-1")})
    assert plan_updates(backend, update_all=True) is None


def test_profile_install_only_missing(monkeypatch):
    monkeypatch.setitem(catalog.PROFILES, "demo", ["nmap", "wifite"])
    change = plan_profile_install(_backend(), "demo")
    assert change is not None
    assert change.argv == ["apt-get", "install", "-y", "wifite"]


def test_profile_install_unknown(capsys):
    assert plan_profile_install(_backend(), "nope") is None
    assert "Unknown profile" in capsys.readouterr().out


def test_profile_remove_only_present(monkeypatch):
    monkeypatch.setitem(catalog.PROFILES, "demo", ["nmap", "wifite"])
    change = plan_profile_remove(_backend(), "demo")
    assert change is not None
    assert change.argv == ["apt-get", "remove", "-y", "nmap"]


def test_plan_upgrade_uses_only_upgrade_flag():
    change = _backend().plan_upgrade(["nmap"])
    assert "--only-upgrade" in change.argv
