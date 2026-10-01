"""Unit tests for the safety guard: dry-run default, --yes gate, audit log."""
from pathlib import Path

from toolkeeper.safety import PlannedChange, SafetyGuard


def _change():
    return PlannedChange(description="test change", argv=["apt-get", "install", "-y", "nmap"])


def test_dry_run_does_not_execute(tmp_path: Path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("subprocess must not run in dry-run mode")

    monkeypatch.setattr("subprocess.run", _boom)
    guard = SafetyGuard(allow_changes=False, log_path=tmp_path / "audit.log")
    assert guard.execute(_change()) == 0
    log = (tmp_path / "audit.log").read_text()
    assert "DRY-RUN" in log


def test_yes_executes_and_logs(tmp_path: Path, monkeypatch):
    calls = []

    class FakeProc:
        returncode = 0

    def _fake_run(argv, **kwargs):
        calls.append(argv)
        return FakeProc()

    monkeypatch.setattr("subprocess.run", _fake_run)
    guard = SafetyGuard(allow_changes=True, log_path=tmp_path / "audit.log")
    assert guard.execute(_change()) == 0
    assert calls == [["apt-get", "install", "-y", "nmap"]]
    log = (tmp_path / "audit.log").read_text()
    assert "EXECUTE" in log and "EXIT=0" in log


def test_exit_code_propagates(tmp_path: Path, monkeypatch):
    class FakeProc:
        returncode = 3

    monkeypatch.setattr("subprocess.run", lambda argv, **kw: FakeProc())
    guard = SafetyGuard(allow_changes=True, log_path=tmp_path / "audit.log")
    assert guard.execute(_change()) == 3
