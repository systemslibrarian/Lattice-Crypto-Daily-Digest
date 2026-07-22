#!/usr/bin/env python3
"""Static site generator for the Lattice Crypto Daily Digest.

Scans the committed daily / weekly / monthly digest markdown files and renders a
self-contained, browsable website into ``site/`` that can be published with
GitHub Pages. The output is fully static (no server, no runtime dependencies)
and is regenerated on every run, so publishing the newest digest is a matter of
re-running this script and deploying ``site/``.

Design goals:

* **Deterministic** – same inputs produce byte-identical output (no timestamps
  baked into content except an explicit build stamp passed via ``--build-date``).
* **Dependency-light** – uses the ``markdown`` package when available and falls
  back to a small built-in renderer so the script never hard-fails a build.
* **CJK-aware** – digests are written in Chinese; fonts, search, and excerpts
  are chosen accordingly.

Usage::

    python scripts/build_site.py --output site
    python scripts/build_site.py --output site --base-url /Lattice-Crypto-Daily-Digest
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent

SITE_TITLE = "格密码科研情报 · Lattice Crypto Research Digest"
SITE_TAGLINE = "Daily retrieval, ranking, and Chinese-language synthesis of lattice cryptography & PQC research."
SITE_REPO_URL = "https://github.com/systemslibrarian/Lattice-Crypto-Daily-Digest"

# --------------------------------------------------------------------------- #
# Internationalisation (UI chrome only; digest bodies stay in their source lang)
# --------------------------------------------------------------------------- #

LANG_DEFAULT = "zh"

# Single source of truth for every translatable UI string. Rendered pages carry
# the default (Chinese) text plus a ``data-i18n`` key; the same dict is shipped
# to the browser so app.js can swap languages client-side without page reloads.
I18N: dict[str, dict[str, str]] = {
    "nav.home": {"zh": "首页", "en": "Home"},
    "nav.daily": {"zh": "日报", "en": "Daily"},
    "nav.weekly": {"zh": "周报", "en": "Weekly"},
    "nav.monthly": {"zh": "月报", "en": "Monthly"},
    "nav.about": {"zh": "关于", "en": "About"},
    "lang.toggle": {"zh": "切换语言", "en": "Switch language"},
    "theme.toggle": {"zh": "切换主题", "en": "Toggle theme"},
    "hero.tag": {"zh": "最新日报", "en": "Latest daily digest"},
    "hero.read": {"zh": "阅读全文 →", "en": "Read →"},
    "hero.archive": {"zh": "全部日报", "en": "All dailies"},
    "stat.selected": {"zh": "最终入选", "en": "Selected"},
    "stat.high": {"zh": "高优先级", "en": "High-priority"},
    "stat.window": {"zh": "检索窗口", "en": "Window"},
    "stat.sources": {"zh": "主要来源", "en": "Sources"},
    "search.label": {"zh": "🔎 搜索全部情报", "en": "🔎 Search all digests"},
    "search.placeholder": {
        "zh": "标题、主题、日期…（如 ML-KEM, LWE, 2026-06）",
        "en": "title, topic, date… (e.g. ML-KEM, LWE, 2026-06)",
    },
    "search.nomatch": {"zh": "未找到匹配结果。", "en": "No matches."},
    "sec.daily.title": {"zh": "日报 Daily", "en": "Daily"},
    "sec.daily.sub": {"zh": "每日格密码 / PQC 论文情报", "en": "Daily lattice / PQC paper intelligence"},
    "sec.weekly.title": {"zh": "周报 Weekly", "en": "Weekly"},
    "sec.weekly.sub": {"zh": "每周研究综述", "en": "Weekly research synthesis"},
    "sec.monthly.title": {"zh": "月报 Monthly", "en": "Monthly"},
    "sec.monthly.sub": {"zh": "月度格密码雷达", "en": "Monthly lattice paper radar"},
    "sec.more": {"zh": "查看全部 →", "en": "View all →"},
    "badge.selected": {"zh": "入选", "en": "Selected"},
    "badge.high": {"zh": "高优", "en": "High"},
    "health.ok": {"zh": "绿色 正常", "en": "Green · healthy"},
    "health.warn": {"zh": "黄色 降级", "en": "Amber · degraded"},
    "health.bad": {"zh": "红色 失败", "en": "Red · failed"},
    "health.unknown": {"zh": "未知", "en": "Unknown"},
    "archive.count": {"zh": "共 %n 期", "en": "%n editions"},
    "empty": {"zh": "暂无内容。", "en": "Nothing here yet."},
    "toc.head": {"zh": "目录 Contents", "en": "Contents"},
    "article.source": {"zh": "查看 markdown 源文件", "en": "View markdown source"},
    "footer.build": {"zh": "由已提交的情报 markdown 生成 · 构建", "en": "Generated from committed digest markdown · Build"},
    "footer.repo": {"zh": "源代码仓库", "en": "Source repository"},
    "footer.rss": {"zh": "RSS 订阅", "en": "RSS feed"},
    "footer.note": {
        "zh": "引用与排序元数据仅供参考。精读前请务必核对原始来源。",
        "en": "Citation and ranking metadata is advisory. Always verify against the primary source before deep reading.",
    },
    "about.title": {"zh": "关于 About", "en": "About"},
    "about.p1": {
        "zh": "本网站是 Lattice Crypto Daily Digest 项目的公开门户，自动把每日、每周、每月生成的格密码 / 后量子密码（PQC）科研情报渲染为可浏览的网页。",
        "en": "This site is the public portal for the Lattice Crypto Daily Digest — it renders the daily, weekly, and monthly lattice / post-quantum cryptography (PQC) research digests into a browsable website.",
    },
    "about.p2": {
        "zh": "每当有新的日报被提交，网站会通过 GitHub Actions 自动重建并更新。",
        "en": "Whenever a new digest is committed, the site is automatically rebuilt and redeployed via GitHub Actions.",
    },
    "about.h.coverage": {"zh": "覆盖范围 Coverage", "en": "Coverage"},
    "about.h.how": {"zh": "工作原理 How it works", "en": "How it works"},
    "about.how.1": {
        "zh": "定时 GitHub Actions 工作流从 IACR ePrint、arXiv、DBLP、Crossref、OpenAlex 和 Semantic Scholar 检索、过滤、排序并去重格密码 / PQC 论文。",
        "en": "A scheduled GitHub Actions workflow retrieves, filters, ranks, and de-duplicates lattice / PQC papers from IACR ePrint, arXiv, DBLP, Crossref, OpenAlex, and Semantic Scholar.",
    },
    "about.how.2": {
        "zh": "生成带日期的中文 markdown 情报（以及 JSON），并提交到仓库。",
        "en": "It writes a dated Chinese-language markdown digest (plus JSON) and commits it to the repository.",
    },
    "about.how.3": {
        "zh": "Pages 工作流从全部已提交的情报重建本网站并发布。",
        "en": "A Pages workflow rebuilds this site from all committed digests and deploys it.",
    },
    "about.h.sources": {"zh": "数据源 Data sources", "en": "Data sources"},
    "about.note": {
        "zh": "排序与引用元数据仅供参考。精读前请务必核对原始来源。",
        "en": "Rankings and citation metadata are advisory only. Always verify against the primary source before deep reading.",
    },
    "about.repo": {"zh": "查看源代码仓库 →", "en": "View the source repository →"},
    "article.langhint": {
        "zh": "情报正文为中文（论文标题与术语保留英文）。",
        "en": "Digest body is in Chinese (paper titles and technical terms stay in English).",
    },
}


def t(key: str) -> str:
    """Render a translatable span: default (Chinese) text + ``data-i18n`` key."""
    entry = I18N[key]
    return f'<span data-i18n="{key}">{html.escape(entry["zh"])}</span>'


def i18n_script() -> str:
    payload = json.dumps(I18N, ensure_ascii=False, separators=(",", ":"))
    return f'<script>window.__I18N__={payload};window.__LANG_DEFAULT__="{LANG_DEFAULT}";</script>'


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

try:  # pragma: no cover - exercised implicitly by the build
    import markdown as _markdown_lib

    _MD = _markdown_lib.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc", "nl2br"],
        output_format="html5",
    )

    def render_markdown(text: str) -> str:
        _MD.reset()
        return _MD.convert(text)

    HAVE_MARKDOWN = True
except Exception:  # pragma: no cover - fallback path
    HAVE_MARKDOWN = False

    def render_markdown(text: str) -> str:
        return _fallback_markdown(text)


def _fallback_markdown(text: str) -> str:
    """Very small markdown subset renderer used only when ``markdown`` is absent.

    Handles headings, unordered lists, tables, links, bold, and paragraphs — the
    constructs the digests actually use. It is intentionally conservative.
    """

    def inline(s: str) -> str:
        s = html.escape(s, quote=False)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        return s

    lines = text.splitlines()
    out: list[str] = []
    i = 0
    list_depth = 0

    def close_lists(target: int) -> None:
        nonlocal list_depth
        while list_depth > target:
            out.append("</ul>")
            list_depth -= 1

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            close_lists(0)
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        # Tables (pipe syntax)
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(
            r"^\|[\s:|-]+\|?$", lines[i + 1].strip()
        ):
            close_lists(0)
            header = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<div class='table-wrap'><table><thead><tr>")
            out.extend(f"<th>{inline(c)}</th>" for c in header)
            out.append("</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue

        indent = len(line) - len(line.lstrip(" "))
        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet:
            depth = indent // 2 + 1
            while list_depth < depth:
                out.append("<ul>")
                list_depth += 1
            close_lists(depth)
            out.append(f"<li>{inline(bullet.group(1))}</li>")
            i += 1
            continue

        if not stripped:
            close_lists(0)
            i += 1
            continue

        close_lists(0)
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    close_lists(0)
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Digest model
# --------------------------------------------------------------------------- #


@dataclass
class Digest:
    kind: str  # daily | weekly | monthly
    slug: str  # e.g. 2026-06-09
    source_path: Path
    title: str
    sort_key: str
    raw: str
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def out_name(self) -> str:
        prefix = {"daily": "d", "weekly": "w", "monthly": "m"}[self.kind]
        return f"{prefix}/{self.slug}.html"

    @property
    def display_date(self) -> str:
        return self.slug


_META_KEYS = {
    "最终入选论文数": "final_count",
    "高优先级论文数": "high_priority",
    "主要来源": "sources",
    "今日主题": "topics",
    "数据源健康": "source_health",
    "检索窗口": "window",
    "run_mode": "run_mode",
    "quality_status": "quality_status",
}


def _parse_daily_meta(raw: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        m = re.match(r"^-\s*([^：:]+)[：:]\s*(.+)$", line.strip())
        if not m:
            continue
        key = m.group(1).strip()
        if key in _META_KEYS:
            meta[_META_KEYS[key]] = m.group(2).strip()
    return meta


def _first_heading(raw: str, fallback: str) -> str:
    for line in raw.splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    return fallback


def _health_state(source_health: str) -> str:
    """Classify overall source health into a css state for the badge."""
    if not source_health:
        return "unknown"
    if "红色" in source_health or "失败" in source_health:
        return "bad"
    if "黄色" in source_health or "降级" in source_health:
        return "warn"
    if "绿色" in source_health or "正常" in source_health:
        return "ok"
    return "unknown"


def load_digests() -> list[Digest]:
    digests: list[Digest] = []

    daily_dir = REPO_ROOT / "digests"
    for path in sorted(daily_dir.glob("*.md")):
        if path.name == ".gitkeep":
            continue
        raw = path.read_text(encoding="utf-8")
        slug = path.stem
        digests.append(
            Digest(
                kind="daily",
                slug=slug,
                source_path=path,
                title=_first_heading(raw, f"日报 {slug}"),
                sort_key=slug,
                raw=raw,
                meta=_parse_daily_meta(raw),
            )
        )

    for path in sorted((daily_dir / "weekly").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        slug = path.stem
        digests.append(
            Digest(
                kind="weekly",
                slug=slug,
                source_path=path,
                title=_first_heading(raw, f"Weekly {slug}"),
                sort_key=slug,
                raw=raw,
            )
        )

    for path in sorted((daily_dir / "monthly").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        slug = path.stem
        digests.append(
            Digest(
                kind="monthly",
                slug=slug,
                source_path=path,
                title=_first_heading(raw, f"Monthly {slug}"),
                sort_key=slug,
                raw=raw,
            )
        )

    return digests


# --------------------------------------------------------------------------- #
# HTML templating (no external template engine)
# --------------------------------------------------------------------------- #


def _rel(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/{path.lstrip('/')}" if base else f"/{path.lstrip('/')}"


def page_shell(
    *,
    base_url: str,
    title: str,
    body: str,
    build_date: str,
    active: str = "",
    description: str = SITE_TAGLINE,
    extra_head: str = "",
) -> str:
    nav_items = [
        ("home", "nav.home", "index.html"),
        ("daily", "nav.daily", "daily.html"),
        ("weekly", "nav.weekly", "weekly.html"),
        ("monthly", "nav.monthly", "monthly.html"),
        ("about", "nav.about", "about.html"),
    ]
    nav = "\n".join(
        f'<a class="nav-link{" active" if key == active else ""}" href="{_rel(base_url, href)}">{t(i18n_key)}</a>'
        for key, i18n_key, href in nav_items
    )
    css = _rel(base_url, "assets/style.css")
    appjs = _rel(base_url, "assets/app.js")
    home = _rel(base_url, "index.html")
    feed = _rel(base_url, "feed.xml")
    return f"""<!DOCTYPE html>
<html lang="zh-Hans" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(description)}">
<meta name="color-scheme" content="light dark">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css}">
<link rel="alternate" type="application/rss+xml" title="Lattice Crypto Digest" href="{feed}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='26'%3E%F0%9F%94%90%3C/text%3E%3C/svg%3E">
{i18n_script()}
{extra_head}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{home}">
      <span class="brand-mark">🔐</span>
      <span class="brand-text">
        <strong>Lattice Crypto Digest</strong>
        <small>格密码科研情报</small>
      </span>
    </a>
    <nav class="site-nav" aria-label="Primary">
      {nav}
    </nav>
    <button class="lang-toggle" type="button" aria-label="Switch language" data-i18n-aria="lang.toggle" title="中文 / English">EN</button>
    <button class="theme-toggle" type="button" aria-label="Toggle color theme" data-i18n-aria="theme.toggle" title="Toggle theme">◐</button>
  </div>
</header>
<main id="main" class="site-main">
{body}
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <p>{t('footer.build')} {html.escape(build_date)}</p>
    <p>
      <a href="{SITE_REPO_URL}">{t('footer.repo')}</a> ·
      <a href="{feed}">{t('footer.rss')}</a>
    </p>
    <p class="footer-note">{t('footer.note')}</p>
  </div>
</footer>
<script src="{appjs}" defer></script>
</body>
</html>
"""


def _stat(label_html: str, value: str, state: str = "") -> str:
    """``label_html`` is trusted markup (typically ``t('...')``)."""
    cls = f"stat stat-{state}" if state else "stat"
    return f'<div class="{cls}"><span class="stat-value">{html.escape(value)}</span><span class="stat-label">{label_html}</span></div>'


def _health_chip(digest: Digest) -> str:
    state = _health_state(digest.meta.get("source_health", ""))
    return f'<span class="chip chip-{state}" title="{html.escape(digest.meta.get("source_health", ""))}">{t("health." + state)}</span>'


def _digest_card(base_url: str, digest: Digest) -> str:
    href = _rel(base_url, digest.out_name)
    meta = digest.meta
    badges = []
    if meta.get("final_count"):
        badges.append(f'<span class="badge">{t("badge.selected")} {html.escape(meta["final_count"])}</span>')
    if meta.get("high_priority") and meta["high_priority"] not in {"0", "无"}:
        badges.append(f'<span class="badge badge-hot">{t("badge.high")} {html.escape(meta["high_priority"])}</span>')
    if meta.get("sources"):
        badges.append(f'<span class="badge badge-muted">{html.escape(meta["sources"])}</span>')
    if digest.kind == "daily" and meta.get("source_health"):
        badges.append(_health_chip(digest))
    topics = meta.get("topics", "")
    topic_html = f'<p class="card-topics">{html.escape(topics)}</p>' if topics else ""
    return f"""<a class="card" href="{href}">
  <div class="card-head">
    <span class="card-date">{html.escape(digest.slug)}</span>
    <span class="card-kind card-kind-{digest.kind}">{digest.kind}</span>
  </div>
  <h3 class="card-title">{html.escape(digest.title)}</h3>
  {topic_html}
  <div class="card-badges">{''.join(badges)}</div>
</a>"""


def render_index(base_url: str, digests: list[Digest], build_date: str) -> str:
    dailies = sorted((d for d in digests if d.kind == "daily"), key=lambda d: d.sort_key, reverse=True)
    weeklies = sorted((d for d in digests if d.kind == "weekly"), key=lambda d: d.sort_key, reverse=True)
    monthlies = sorted((d for d in digests if d.kind == "monthly"), key=lambda d: d.sort_key, reverse=True)

    latest = dailies[0] if dailies else None
    hero = ""
    if latest:
        m = latest.meta
        stats = "".join(
            [
                _stat(t("stat.selected"), m.get("final_count", "—")),
                _stat(t("stat.high"), m.get("high_priority", "—"), "hot" if m.get("high_priority") not in {None, "0", "无"} else ""),
                _stat(t("stat.window"), m.get("window", "—")),
                _stat(t("stat.sources"), m.get("sources", "—")),
            ]
        )
        hero = f"""<section class="hero">
  <div class="hero-tag">{t('hero.tag')}</div>
  <h1 class="hero-title">{html.escape(latest.title)}</h1>
  <p class="hero-topics">{html.escape(m.get('topics', ''))}</p>
  <div class="hero-stats">{stats}</div>
  <div class="hero-actions">
    <a class="btn btn-primary" href="{_rel(base_url, latest.out_name)}">{t('hero.read')}</a>
    <a class="btn" href="{_rel(base_url, 'daily.html')}">{t('hero.archive')}</a>
  </div>
</section>"""

    def grid(prefix: str, items: list[Digest], more_href: str) -> str:
        if not items:
            return ""
        cards = "\n".join(_digest_card(base_url, d) for d in items[:6])
        more = f'<a class="section-more" href="{_rel(base_url, more_href)}">{t("sec.more")}</a>' if len(items) > 6 else ""
        return f"""<section class="section">
  <div class="section-head">
    <div><h2 class="section-title">{t(prefix + '.title')}</h2><p class="section-sub">{t(prefix + '.sub')}</p></div>
    {more}
  </div>
  <div class="card-grid">{cards}</div>
</section>"""

    search = f"""<section class="search-block">
  <label class="search-label" for="site-search">{t('search.label')}</label>
  <input id="site-search" class="search-input" type="search" placeholder="标题、主题、日期…（如 ML-KEM, LWE, 2026-06）" data-i18n-placeholder="search.placeholder" autocomplete="off" data-search-url="{_rel(base_url, 'search-index.json')}">
  <div id="search-results" class="search-results" hidden></div>
</section>"""

    body = "\n".join(
        [
            hero,
            search,
            grid("sec.daily", dailies, "daily.html"),
            grid("sec.weekly", weeklies, "weekly.html"),
            grid("sec.monthly", monthlies, "monthly.html"),
        ]
    )
    return page_shell(
        base_url=base_url,
        title=SITE_TITLE,
        body=body,
        build_date=build_date,
        active="home",
    )


def render_archive(base_url: str, kind: str, digests: list[Digest], build_date: str) -> str:
    title_key = {"daily": "sec.daily.title", "weekly": "sec.weekly.title", "monthly": "sec.monthly.title"}[kind]
    items = sorted((d for d in digests if d.kind == kind), key=lambda d: d.sort_key, reverse=True)
    label_zh = I18N[title_key]["zh"]
    cards = "\n".join(_digest_card(base_url, d) for d in items) or f'<p class="empty">{t("empty")}</p>'
    count = f'<span data-i18n="archive.count" data-n="{len(items)}">共 {len(items)} 期</span>'
    body = f"""<section class="section">
  <div class="section-head"><div><h1 class="section-title">{t(title_key)}</h1><p class="section-sub">{count}</p></div></div>
  <div class="card-grid">{cards}</div>
</section>"""
    return page_shell(base_url=base_url, title=f"{label_zh} · {SITE_TITLE}", body=body, build_date=build_date, active=kind)


def _build_toc(html_body: str) -> str:
    """Extract h2/h3 headings that carry an id (markdown 'toc' extension adds them)."""
    entries = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h[23]>', html_body, flags=re.S)
    if not entries:
        return ""
    items = []
    for level, hid, text in entries:
        clean = re.sub(r"<[^>]+>", "", text).strip()
        items.append(f'<li class="toc-l{level}"><a href="#{hid}">{html.escape(clean)}</a></li>')
    return f'<nav class="toc" aria-label="Contents"><p class="toc-head">{t("toc.head")}</p><ul>{"".join(items)}</ul></nav>'


def render_digest_page(base_url: str, digest: Digest, prev: Digest | None, nxt: Digest | None, build_date: str) -> str:
    content_html = render_markdown(digest.raw)
    # Drop the leading H1 (we render our own title header) to avoid duplication.
    content_html = re.sub(r"^\s*<h1[^>]*>.*?</h1>", "", content_html, count=1, flags=re.S)
    toc = _build_toc(content_html)

    kind_home = {"daily": "daily.html", "weekly": "weekly.html", "monthly": "monthly.html"}[digest.kind]
    prev_link = f'<a class="pager-prev" href="{_rel(base_url, prev.out_name)}">← {html.escape(prev.slug)}</a>' if prev else "<span></span>"
    next_link = f'<a class="pager-next" href="{_rel(base_url, nxt.out_name)}">{html.escape(nxt.slug)} →</a>' if nxt else "<span></span>"

    meta_chips = ""
    if digest.kind == "daily" and digest.meta:
        chips = []
        if digest.meta.get("run_mode"):
            chips.append(f'<span class="chip">{html.escape(digest.meta["run_mode"])}</span>')
        if digest.meta.get("quality_status"):
            chips.append(f'<span class="chip">{html.escape(digest.meta["quality_status"])}</span>')
        if digest.meta.get("source_health"):
            chips.append(_health_chip(digest))
        meta_chips = f'<div class="article-chips">{"".join(chips)}</div>'

    body = f"""<article class="article">
  <div class="article-head">
    <a class="crumb" href="{_rel(base_url, kind_home)}">← {digest.kind}</a>
    <h1 class="article-title">{html.escape(digest.title)}</h1>
    {meta_chips}
    <p class="article-langhint">{t('article.langhint')}</p>
    <p class="article-source"><a href="{SITE_REPO_URL}/blob/main/{digest.source_path.relative_to(REPO_ROOT).as_posix()}">{t('article.source')}</a></p>
  </div>
  <div class="article-layout">
    {toc}
    <div class="article-body markdown-body">
      {content_html}
    </div>
  </div>
  <nav class="pager">{prev_link}{next_link}</nav>
</article>"""
    return page_shell(
        base_url=base_url,
        title=f"{digest.title} · {SITE_TITLE}",
        body=body,
        build_date=build_date,
        active=digest.kind,
        description=digest.meta.get("topics", SITE_TAGLINE),
    )


def render_about(base_url: str, digests: list[Digest], build_date: str) -> str:
    counts = {k: sum(1 for d in digests if d.kind == k) for k in ("daily", "weekly", "monthly")}
    body = f"""<section class="section prose">
  <h1 class="section-title">{t('about.title')}</h1>
  <p>{t('about.p1')}</p>
  <p>{t('about.p2')}</p>
  <h2>{t('about.h.coverage')}</h2>
  <div class="hero-stats">
    {_stat(t('nav.daily'), str(counts['daily']))}
    {_stat(t('nav.weekly'), str(counts['weekly']))}
    {_stat(t('nav.monthly'), str(counts['monthly']))}
  </div>
  <h2>{t('about.h.how')}</h2>
  <ol>
    <li>{t('about.how.1')}</li>
    <li>{t('about.how.2')}</li>
    <li>{t('about.how.3')}</li>
  </ol>
  <h2>{t('about.h.sources')}</h2>
  <ul>
    <li>IACR ePrint · arXiv · DBLP · Crossref · OpenAlex · Semantic Scholar</li>
  </ul>
  <p class="footer-note">{t('about.note')}</p>
  <p><a class="btn" href="{SITE_REPO_URL}">{t('about.repo')}</a></p>
</section>"""
    return page_shell(base_url=base_url, title=f"About · {SITE_TITLE}", body=body, build_date=build_date, active="about")


# --------------------------------------------------------------------------- #
# Search index + RSS
# --------------------------------------------------------------------------- #


def _plain_excerpt(raw: str, limit: int = 260) -> str:
    text = re.sub(r"[#>*`|_-]", " ", raw)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def build_search_index(base_url: str, digests: list[Digest]) -> str:
    records = []
    for d in sorted(digests, key=lambda x: x.sort_key, reverse=True):
        records.append(
            {
                "title": d.title,
                "kind": d.kind,
                "date": d.slug,
                "url": _rel(base_url, d.out_name),
                "topics": d.meta.get("topics", ""),
                "excerpt": _plain_excerpt(d.raw),
            }
        )
    return json.dumps(records, ensure_ascii=False, separators=(",", ":"))


def build_feed(base_url: str, digests: list[Digest], build_date: str) -> str:
    site = SITE_REPO_URL
    items = []
    ordered = sorted(digests, key=lambda d: d.sort_key, reverse=True)[:40]
    for d in ordered:
        link = _rel(base_url, d.out_name)
        # Make link absolute if base_url looks like a full origin isn't known; keep relative-safe.
        desc = html.escape(_plain_excerpt(d.raw, 400))
        items.append(
            f"""    <item>
      <title>{html.escape(d.title)}</title>
      <link>{html.escape(link)}</link>
      <guid isPermaLink="false">{html.escape(d.kind + ':' + d.slug)}</guid>
      <category>{d.kind}</category>
      <description>{desc}</description>
    </item>"""
        )
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{html.escape(SITE_TITLE)}</title>
    <link>{site}</link>
    <description>{html.escape(SITE_TAGLINE)}</description>
    <language>zh-Hans</language>
    <lastBuildDate>{html.escape(build_date)}</lastBuildDate>
{body}
  </channel>
</rss>
"""


# --------------------------------------------------------------------------- #
# Build orchestration
# --------------------------------------------------------------------------- #


def build_site(output: Path, base_url: str, build_date: str) -> dict[str, int]:
    digests = load_digests()

    output.mkdir(parents=True, exist_ok=True)
    (output / "d").mkdir(exist_ok=True)
    (output / "w").mkdir(exist_ok=True)
    (output / "m").mkdir(exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)

    # Prevent GitHub Pages Jekyll from mangling files/underscore dirs.
    (output / ".nojekyll").write_text("", encoding="utf-8")

    # Copy assets from the repo's site-src if present, else write the bundled ones.
    _write_assets(output / "assets")

    (output / "index.html").write_text(render_index(base_url, digests, build_date), encoding="utf-8")
    (output / "daily.html").write_text(render_archive(base_url, "daily", digests, build_date), encoding="utf-8")
    (output / "weekly.html").write_text(render_archive(base_url, "weekly", digests, build_date), encoding="utf-8")
    (output / "monthly.html").write_text(render_archive(base_url, "monthly", digests, build_date), encoding="utf-8")
    (output / "about.html").write_text(render_about(base_url, digests, build_date), encoding="utf-8")

    # Per-kind ordered lists for prev/next navigation.
    by_kind: dict[str, list[Digest]] = {"daily": [], "weekly": [], "monthly": []}
    for d in digests:
        by_kind[d.kind].append(d)
    for kind, items in by_kind.items():
        ordered = sorted(items, key=lambda d: d.sort_key)  # ascending
        for idx, d in enumerate(ordered):
            prev = ordered[idx - 1] if idx > 0 else None
            nxt = ordered[idx + 1] if idx + 1 < len(ordered) else None
            (output / d.out_name).write_text(
                render_digest_page(base_url, d, prev, nxt, build_date), encoding="utf-8"
            )

    (output / "search-index.json").write_text(build_search_index(base_url, digests), encoding="utf-8")
    (output / "feed.xml").write_text(build_feed(base_url, digests, build_date), encoding="utf-8")

    return {k: len(v) for k, v in by_kind.items()}


def _write_assets(assets_dir: Path) -> None:
    (assets_dir / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (assets_dir / "app.js").write_text(APP_JS, encoding="utf-8")


# Assets are imported from sibling module files so this generator stays readable.
from site_assets import APP_JS, STYLE_CSS  # noqa: E402  (defined below in scripts/site_assets.py)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Lattice Crypto Digest website.")
    parser.add_argument("--output", default="site", help="Output directory (default: site)")
    parser.add_argument(
        "--base-url",
        default="",
        help="Base URL path the site is served from, e.g. /Lattice-Crypto-Daily-Digest for project pages.",
    )
    parser.add_argument(
        "--build-date",
        default=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        help="Build stamp shown in the footer (kept explicit for deterministic builds/tests).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output

    counts = build_site(output, args.base_url.rstrip("/"), args.build_date)
    total = sum(counts.values())
    renderer = "markdown" if HAVE_MARKDOWN else "builtin-fallback"
    print(
        f"Built site -> {output} | daily={counts['daily']} weekly={counts['weekly']} "
        f"monthly={counts['monthly']} total={total} | renderer={renderer}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
