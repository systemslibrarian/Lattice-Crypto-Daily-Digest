from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

build_site = importlib.import_module("build_site")


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("site")
    build_site.build_site(out, base_url="/Lattice-Crypto-Daily-Digest", build_date="2026-07-22 00:00 UTC")
    return out


def test_core_pages_exist(built: Path) -> None:
    for name in ("index.html", "daily.html", "weekly.html", "monthly.html", "about.html"):
        assert (built / name).is_file(), f"missing top-level page {name}"
    assert (built / ".nojekyll").is_file()
    assert (built / "assets" / "style.css").is_file()
    assert (built / "assets" / "app.js").is_file()
    assert (built / "search-index.json").is_file()
    assert (built / "feed.xml").is_file()


def test_every_digest_renders_a_page(built: Path) -> None:
    digests = build_site.load_digests()
    assert digests, "expected at least one committed digest"
    for digest in digests:
        page = built / digest.out_name
        assert page.is_file(), f"missing rendered page for {digest.slug}"
        text = page.read_text(encoding="utf-8")
        assert digest.title in text


def test_daily_metadata_is_parsed() -> None:
    dailies = [d for d in build_site.load_digests() if d.kind == "daily"]
    assert dailies
    # At least one daily should expose the paper-count metadata we surface on cards.
    assert any(d.meta.get("final_count") for d in dailies), "final_count never parsed"


def test_search_index_is_valid_json(built: Path) -> None:
    records = json.loads((built / "search-index.json").read_text(encoding="utf-8"))
    assert isinstance(records, list) and records
    sample = records[0]
    for key in ("title", "kind", "date", "url", "excerpt"):
        assert key in sample
    assert sample["url"].startswith("/Lattice-Crypto-Daily-Digest/")


def test_base_url_is_applied(built: Path) -> None:
    index = (built / "index.html").read_text(encoding="utf-8")
    assert "/Lattice-Crypto-Daily-Digest/assets/style.css" in index


def test_language_toggle_is_wired(built: Path) -> None:
    index = (built / "index.html").read_text(encoding="utf-8")
    assert "window.__I18N__" in index
    assert 'class="lang-toggle"' in index
    assert "data-i18n=" in index
    # Digest pages also carry the toggle and the i18n payload.
    digest_page = next((built / "d").glob("*.html"))
    body = digest_page.read_text(encoding="utf-8")
    assert 'class="lang-toggle"' in body
    assert "window.__I18N__" in body


def test_every_i18n_key_has_both_languages() -> None:
    for key, entry in build_site.I18N.items():
        assert "zh" in entry and entry["zh"], f"{key} missing zh"
        assert "en" in entry and entry["en"], f"{key} missing en"


def test_latest_daily_is_featured(built: Path) -> None:
    dailies = sorted(
        (d for d in build_site.load_digests() if d.kind == "daily"),
        key=lambda d: d.sort_key,
    )
    latest = dailies[-1]
    index = (built / "index.html").read_text(encoding="utf-8")
    assert latest.title in index
    assert "hero" in index
