"""Byte-exact HTTP replay tests for the ``lattice_digest.http`` layer.

Unlike ``test_source_429_does_not_crash.py`` — which monkey-patches
``lattice_digest.http.urlopen`` at the interface tier — these tests replay
hand-authored cassettes through the *real* urllib stack via vcrpy. That means
the genuine ``http.client`` → ``urllib.request`` → ``HTTPError`` path runs,
including status parsing, ``Retry-After`` handling, and the retry/backoff loop.
The cassettes live in ``tests/cassettes/`` and are replayed with
``record_mode="none"`` so the suite never touches the network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

vcr = pytest.importorskip("vcr")

from lattice_digest.http import request_json, request_text  # noqa: E402

CASSETTES = Path(__file__).resolve().parent / "cassettes"
URL = "https://api.example.test/works"

_VCR = vcr.VCR(cassette_library_dir=str(CASSETTES), record_mode="none")


def _kwargs(cache_dir: Path) -> dict:
    return dict(
        source="example",
        user_agent="lcd-test",
        cache_dir=cache_dir,
        min_interval_seconds=0,
        max_retries=1,
        sleep_func=lambda _delay: None,  # never actually sleep during backoff
    )


def test_rate_limit_exhausts_retries_through_real_stack(tmp_path: Path) -> None:
    with _VCR.use_cassette("rate_limited_429.yaml"):
        resp = request_text(URL, **_kwargs(tmp_path))

    assert resp.ok is False
    assert resp.warning is not None
    assert resp.warning.status_code == 429
    # Retry-After: 7 must survive the genuine header-parsing path.
    assert resp.warning.retry_after == 7.0
    # max_retries=1 -> two attempts before giving up.
    assert resp.warning.attempts == 2
    assert "rate limited" in (resp.warning.response_body_preview or "")
    assert "HTTP 429" in resp.warning.to_message()


def test_transient_503_then_recovers(tmp_path: Path) -> None:
    with _VCR.use_cassette("retry_503_then_200.yaml"):
        data, resp = request_json(URL, **_kwargs(tmp_path))

    assert resp.ok is True
    assert data == {"results": [{"id": "W1"}]}


def test_replay_is_offline_only(tmp_path: Path) -> None:
    # A request with no matching interaction must fail loudly rather than hit the
    # network — proving record_mode="none" gives deterministic, offline replay.
    with pytest.raises(Exception):
        with _VCR.use_cassette("retry_503_then_200.yaml"):
            request_text("https://api.example.test/unrecorded", **_kwargs(tmp_path))
