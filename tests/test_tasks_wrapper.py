from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

invoke = pytest.importorskip("invoke")
tasks = importlib.import_module("tasks")


def _collection():
    return invoke.Collection.from_module(tasks)


def test_blessed_tasks_are_registered() -> None:
    names = set(_collection().task_names)
    for expected in {"daily", "daily-run", "weekly", "full", "backfill", "build-site", "ci", "test"}:
        assert expected in names, f"task '{expected}' not registered"


def test_plan_and_run_are_distinct() -> None:
    # The safe model: `daily` plans, `daily-run` executes. Both must exist so an
    # operator never has to hand-assemble the --execute flag matrix.
    names = set(_collection().task_names)
    assert "daily" in names and "daily-run" in names


def test_daily_run_encodes_execute_flags() -> None:
    calls: list[str] = []

    class FakeCtx:
        def run(self, command, **kwargs):
            calls.append(command)

    tasks.daily_run.body(FakeCtx())
    assert calls, "daily_run issued no command"
    cmd = calls[0]
    for token in ("workflow daily", "--execute", "--since 36h", "--output markdown,json", "--send none"):
        assert token in cmd, f"missing {token!r} in blessed daily-run command"


def test_backfill_requires_a_date() -> None:
    class FakeCtx:
        def run(self, command, **kwargs):
            raise AssertionError("backfill must not run a command without a date")

    with pytest.raises(SystemExit):
        tasks.backfill.body(FakeCtx(), date="")
