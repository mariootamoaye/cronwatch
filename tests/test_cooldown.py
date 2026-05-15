"""Tests for cronwatch.cooldown."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.cooldown import (
    CooldownEntry,
    clear_cooldown,
    is_cooling_down,
    record_alert,
)


@pytest.fixture()
def cooldown_file(tmp_path: Path) -> Path:
    return tmp_path / "cooldown.json"


def _ts(offset_seconds: int = 0) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(seconds=offset_seconds)


# ---------------------------------------------------------------------------
# CooldownEntry unit tests
# ---------------------------------------------------------------------------

def test_entry_is_cooling_down_within_window():
    entry = CooldownEntry("backup", last_alerted=_ts(-30), window_seconds=120)
    assert entry.is_cooling_down() is True


def test_entry_not_cooling_down_after_window():
    entry = CooldownEntry("backup", last_alerted=_ts(-200), window_seconds=120)
    assert entry.is_cooling_down() is False


def test_entry_not_cooling_down_at_exact_boundary():
    base = _ts(-120)
    entry = CooldownEntry("backup", last_alerted=base, window_seconds=120)
    # exactly at expiry — should NOT be cooling down
    assert entry.is_cooling_down(at=base + timedelta(seconds=120)) is False


def test_entry_round_trip():
    entry = CooldownEntry("nightly", last_alerted=_ts(), window_seconds=300)
    restored = CooldownEntry.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.window_seconds == entry.window_seconds
    assert abs((restored.last_alerted - entry.last_alerted).total_seconds()) < 1


# ---------------------------------------------------------------------------
# record_alert / is_cooling_down / clear_cooldown
# ---------------------------------------------------------------------------

def test_record_alert_creates_file(cooldown_file: Path):
    record_alert("myjob", window_seconds=60, path=cooldown_file)
    assert cooldown_file.exists()


def test_is_cooling_down_after_record(cooldown_file: Path):
    record_alert("myjob", window_seconds=600, path=cooldown_file)
    assert is_cooling_down("myjob", cooldown_file) is True


def test_is_not_cooling_down_without_record(cooldown_file: Path):
    assert is_cooling_down("unknown", cooldown_file) is False


def test_is_not_cooling_down_after_window_expires(cooldown_file: Path):
    record_alert("oldjob", window_seconds=10, path=cooldown_file)
    future = _ts(+20)
    assert is_cooling_down("oldjob", cooldown_file, at=future) is False


def test_record_alert_overwrites_existing_entry(cooldown_file: Path):
    record_alert("job", window_seconds=5, path=cooldown_file)
    record_alert("job", window_seconds=600, path=cooldown_file)
    # second call should refresh the window
    assert is_cooling_down("job", cooldown_file) is True
    import json
    data = json.loads(cooldown_file.read_text())
    assert len(data) == 1  # only one entry per job


def test_clear_cooldown_removes_entry(cooldown_file: Path):
    record_alert("job", window_seconds=600, path=cooldown_file)
    removed = clear_cooldown("job", cooldown_file)
    assert removed is True
    assert is_cooling_down("job", cooldown_file) is False


def test_clear_cooldown_returns_false_when_not_present(cooldown_file: Path):
    assert clear_cooldown("ghost", cooldown_file) is False
