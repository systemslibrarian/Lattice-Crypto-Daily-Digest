from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mypy_config() -> dict:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data.get("tool", {}).get("mypy", {})


def test_mypy_is_configured_strict() -> None:
    cfg = _mypy_config()
    assert cfg.get("strict") is True, "mypy strict mode must stay enabled"
    assert cfg.get("mypy_path") == "src"


def test_mypy_allowlist_is_nonempty_and_exists() -> None:
    cfg = _mypy_config()
    files = cfg.get("files", [])
    assert files, "mypy allowlist must not be empty (the ratchet needs a floor)"
    for relative in files:
        assert (ROOT / relative).is_file(), f"mypy allowlist references missing file: {relative}"


def test_ci_runs_mypy() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "mypy" in ci, "CI must run the mypy type gate"
