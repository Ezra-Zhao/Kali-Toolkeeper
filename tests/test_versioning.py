"""Unit tests for Debian version comparison."""
from toolkeeper.versioning import debian_compare


def test_simple_upgrade():
    assert debian_compare("7.94+dfsg1-1", "7.95+dfsg1-1") < 0


def test_revision_bump():
    assert debian_compare("1:2.5.0-1", "1:2.5.0-2") < 0


def test_equal():
    assert debian_compare("1.8.3-1", "1.8.3-1") == 0


def test_epoch_wins():
    # 1:1.0 beats 2.0 because epoch 1 > epoch 0
    assert debian_compare("1:1.0", "2.0") > 0


def test_tilde_sorts_before_release():
    assert debian_compare("1.0~beta1", "1.0") < 0


def test_kali_style_versions():
    assert debian_compare("6.3.31-0kali1", "6.4.5-0kali1") < 0
    assert debian_compare("2024.8.2-0kali1", "2024.8.2-0kali1") == 0


def test_numeric_not_lexical():
    # 1.10 > 1.9 numerically (lexically "1.10" < "1.9")
    assert debian_compare("1.9-1", "1.10-1") < 0
