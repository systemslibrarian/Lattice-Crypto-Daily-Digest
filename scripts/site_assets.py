"""Static assets (CSS + JS) for the digest website.

Kept in a separate module so :mod:`build_site` stays focused on structure. These
strings are written verbatim into ``site/assets/`` at build time.
"""

from __future__ import annotations

STYLE_CSS = r""":root {
  --bg: #f7f8fb;
  --surface: #ffffff;
  --surface-2: #f0f2f7;
  --text: #14181f;
  --text-soft: #55606f;
  --border: #e2e6ee;
  --accent: #4338ca;
  --accent-soft: #eef0fe;
  --hot: #c2410c;
  --hot-soft: #fff2ea;
  --ok: #15803d;
  --ok-soft: #e7f6ec;
  --warn: #b45309;
  --warn-soft: #fdf3e2;
  --bad: #b91c1c;
  --bad-soft: #fdeaea;
  --shadow: 0 1px 2px rgba(16,24,40,.06), 0 8px 24px rgba(16,24,40,.06);
  --radius: 14px;
  --maxw: 1080px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", Roboto, Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", ui-monospace, "JetBrains Mono", Consolas, "Liberation Mono", monospace;
}
html[data-theme="dark"], :root[data-theme="dark"] {
  --bg: #0d1017;
  --surface: #161b25;
  --surface-2: #1e2430;
  --text: #e7ecf3;
  --text-soft: #9aa6b6;
  --border: #262d3a;
  --accent: #a5b4fc;
  --accent-soft: #1e2436;
  --hot: #fb923c;
  --hot-soft: #33220f;
  --ok: #4ade80;
  --ok-soft: #12261a;
  --warn: #fbbf24;
  --warn-soft: #2c2410;
  --bad: #f87171;
  --bad-soft: #2c1414;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.35);
}
@media (prefers-color-scheme: dark) {
  :root[data-theme="auto"] {
    --bg: #0d1017; --surface: #161b25; --surface-2: #1e2430; --text: #e7ecf3;
    --text-soft: #9aa6b6; --border: #262d3a; --accent: #a5b4fc; --accent-soft: #1e2436;
    --hot: #fb923c; --hot-soft: #33220f; --ok: #4ade80; --ok-soft: #12261a;
    --warn: #fbbf24; --warn-soft: #2c2410; --bad: #f87171; --bad-soft: #2c1414;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.35);
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; background: var(--bg); color: var(--text); font-family: var(--font);
  line-height: 1.65; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.skip-link {
  position: absolute; left: -999px; top: 0; background: var(--accent); color: #fff;
  padding: .5rem 1rem; border-radius: 0 0 8px 0; z-index: 100;
}
.skip-link:focus { left: 0; }

/* Header */
.site-header {
  position: sticky; top: 0; z-index: 50; background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: saturate(1.4) blur(10px); border-bottom: 1px solid var(--border);
}
.header-inner {
  max-width: var(--maxw); margin: 0 auto; padding: .6rem 1.2rem; display: flex;
  align-items: center; gap: 1rem;
}
.brand { display: flex; align-items: center; gap: .6rem; color: var(--text); }
.brand:hover { text-decoration: none; }
.brand-mark { font-size: 1.5rem; }
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-text small { color: var(--text-soft); font-size: .72rem; letter-spacing: .02em; }
.site-nav { display: flex; gap: .2rem; margin-left: auto; flex-wrap: wrap; }
.nav-link {
  color: var(--text-soft); padding: .35rem .7rem; border-radius: 8px; font-size: .9rem; font-weight: 500;
}
.nav-link:hover { background: var(--surface-2); color: var(--text); text-decoration: none; }
.nav-link.active { color: var(--accent); background: var(--accent-soft); }
.theme-toggle {
  border: 1px solid var(--border); background: var(--surface); color: var(--text);
  width: 36px; height: 36px; border-radius: 9px; cursor: pointer; font-size: 1rem;
}
.theme-toggle:hover { background: var(--surface-2); }

/* Layout */
.site-main { max-width: var(--maxw); margin: 0 auto; padding: 1.6rem 1.2rem 3rem; }
.section { margin: 2.4rem 0; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.section-title { font-size: 1.35rem; margin: 0; }
.section-sub { margin: .15rem 0 0; color: var(--text-soft); font-size: .9rem; }
.section-more { font-size: .9rem; white-space: nowrap; }
.empty { color: var(--text-soft); }

/* Hero */
.hero {
  background: linear-gradient(135deg, var(--accent-soft), var(--surface));
  border: 1px solid var(--border); border-radius: var(--radius); padding: 2rem;
  box-shadow: var(--shadow);
}
.hero-tag { color: var(--accent); font-weight: 600; font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }
.hero-title { font-size: 1.8rem; margin: .5rem 0 .4rem; line-height: 1.25; }
.hero-topics { color: var(--text-soft); margin: 0 0 1.2rem; }
.hero-stats { display: flex; flex-wrap: wrap; gap: .8rem; margin-bottom: 1.4rem; }
.stat {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: .6rem .9rem; min-width: 96px; display: flex; flex-direction: column;
}
.stat-value { font-size: 1.3rem; font-weight: 700; }
.stat-label { font-size: .72rem; color: var(--text-soft); text-transform: uppercase; letter-spacing: .04em; }
.stat-hot .stat-value { color: var(--hot); }
.hero-actions { display: flex; gap: .6rem; flex-wrap: wrap; }
.btn {
  display: inline-block; padding: .55rem 1.05rem; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); font-weight: 600; font-size: .92rem; cursor: pointer;
}
.btn:hover { text-decoration: none; border-color: var(--accent); }
.btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
html[data-theme="dark"] .btn-primary, :root[data-theme="dark"] .btn-primary { color: #0d1017; }

/* Search */
.search-block { margin: 2rem 0; }
.search-label { display: block; font-weight: 600; margin-bottom: .5rem; }
.search-input {
  width: 100%; padding: .8rem 1rem; font-size: 1rem; border-radius: 12px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); font-family: var(--font);
}
.search-input:focus { outline: 2px solid var(--accent); border-color: var(--accent); }
.search-results { margin-top: .6rem; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--surface); }
.search-hit { display: block; padding: .7rem 1rem; border-bottom: 1px solid var(--border); color: var(--text); }
.search-hit:last-child { border-bottom: none; }
.search-hit:hover { background: var(--surface-2); text-decoration: none; }
.search-hit .sh-title { font-weight: 600; }
.search-hit .sh-meta { font-size: .78rem; color: var(--text-soft); }
.search-empty { padding: .8rem 1rem; color: var(--text-soft); }

/* Cards */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
.card {
  display: flex; flex-direction: column; gap: .4rem; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.1rem; color: var(--text); box-shadow: var(--shadow);
  transition: transform .12s ease, border-color .12s ease;
}
.card:hover { text-decoration: none; transform: translateY(-2px); border-color: var(--accent); }
.card-head { display: flex; align-items: center; justify-content: space-between; }
.card-date { font-family: var(--mono); font-size: .8rem; color: var(--text-soft); }
.card-kind { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; padding: .12rem .5rem; border-radius: 999px; background: var(--surface-2); color: var(--text-soft); }
.card-kind-daily { background: var(--accent-soft); color: var(--accent); }
.card-title { font-size: 1.02rem; margin: .1rem 0; line-height: 1.35; }
.card-topics { margin: 0; color: var(--text-soft); font-size: .85rem; }
.card-badges { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: auto; padding-top: .4rem; }
.badge { font-size: .72rem; padding: .12rem .5rem; border-radius: 6px; background: var(--surface-2); color: var(--text-soft); }
.badge-hot { background: var(--hot-soft); color: var(--hot); font-weight: 600; }
.badge-muted { background: transparent; border: 1px dashed var(--border); }
.chip { font-size: .72rem; padding: .12rem .5rem; border-radius: 6px; background: var(--surface-2); color: var(--text-soft); }
.chip-ok { background: var(--ok-soft); color: var(--ok); }
.chip-warn { background: var(--warn-soft); color: var(--warn); }
.chip-bad { background: var(--bad-soft); color: var(--bad); }

/* Article */
.article { margin-top: 1rem; }
.article-head { border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 1.4rem; }
.crumb { font-size: .85rem; color: var(--text-soft); }
.article-title { font-size: 1.7rem; margin: .5rem 0; line-height: 1.3; }
.article-chips { display: flex; gap: .4rem; flex-wrap: wrap; margin: .5rem 0; }
.article-source { font-size: .82rem; margin: .2rem 0 0; }
.article-layout { display: grid; grid-template-columns: 240px 1fr; gap: 2rem; align-items: start; }
.toc {
  position: sticky; top: 72px; font-size: .85rem; border: 1px solid var(--border); border-radius: 12px;
  padding: 1rem; background: var(--surface); max-height: calc(100vh - 100px); overflow: auto;
}
.toc-head { margin: 0 0 .5rem; font-weight: 700; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; color: var(--text-soft); }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { margin: .15rem 0; }
.toc-l3 { padding-left: .8rem; }
.toc a { color: var(--text-soft); }
.toc a:hover { color: var(--accent); }

/* Markdown body */
.markdown-body { min-width: 0; }
.markdown-body h2 { font-size: 1.35rem; margin: 2rem 0 .8rem; padding-top: .4rem; border-top: 1px solid var(--border); }
.markdown-body h2:first-child { border-top: none; padding-top: 0; margin-top: 0; }
.markdown-body h3 { font-size: 1.12rem; margin: 1.4rem 0 .6rem; }
.markdown-body h4 { font-size: 1rem; margin: 1.1rem 0 .5rem; color: var(--text-soft); }
.markdown-body p { margin: .6rem 0; }
.markdown-body ul, .markdown-body ol { padding-left: 1.4rem; }
.markdown-body li { margin: .25rem 0; }
.markdown-body code { font-family: var(--mono); background: var(--surface-2); padding: .1rem .35rem; border-radius: 5px; font-size: .88em; }
.markdown-body pre { background: var(--surface-2); padding: 1rem; border-radius: 10px; overflow: auto; }
.markdown-body pre code { background: none; padding: 0; }
.markdown-body blockquote { border-left: 3px solid var(--accent); margin: .8rem 0; padding: .2rem 1rem; color: var(--text-soft); }
.markdown-body a { word-break: break-word; }
.table-wrap { overflow-x: auto; margin: 1rem 0; }
.markdown-body table { border-collapse: collapse; width: 100%; font-size: .88rem; }
.markdown-body th, .markdown-body td { border: 1px solid var(--border); padding: .45rem .6rem; text-align: left; }
.markdown-body thead th { background: var(--surface-2); }
.markdown-body tbody tr:nth-child(even) td { background: var(--surface-2); }

/* Pager */
.pager { display: flex; justify-content: space-between; margin-top: 2.4rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: .9rem; }

/* Prose (about) */
.prose { max-width: 760px; }
.prose h2 { margin-top: 1.8rem; }

/* Footer */
.site-footer { border-top: 1px solid var(--border); background: var(--surface); }
.footer-inner { max-width: var(--maxw); margin: 0 auto; padding: 1.6rem 1.2rem; color: var(--text-soft); font-size: .85rem; }
.footer-inner p { margin: .3rem 0; }
.footer-note { font-size: .8rem; opacity: .85; }

@media (max-width: 760px) {
  .article-layout { grid-template-columns: 1fr; }
  .toc { position: static; max-height: none; }
  .hero-title { font-size: 1.45rem; }
}
"""

APP_JS = r"""(function () {
  // ---- Theme toggle -------------------------------------------------------
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('lcd-theme'); } catch (e) {}
  if (stored) root.setAttribute('data-theme', stored);

  var toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = root.getAttribute('data-theme');
      var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      // auto -> opposite of system, then explicit light/dark toggle
      var next;
      if (current === 'auto') next = prefersDark ? 'light' : 'dark';
      else if (current === 'dark') next = 'light';
      else next = 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('lcd-theme', next); } catch (e) {}
    });
  }

  // ---- Search -------------------------------------------------------------
  var input = document.getElementById('site-search');
  var results = document.getElementById('search-results');
  if (!input || !results) return;

  var index = null;
  var loading = false;

  function loadIndex() {
    if (index || loading) return;
    loading = true;
    fetch(input.getAttribute('data-search-url'))
      .then(function (r) { return r.json(); })
      .then(function (data) { index = data; render(input.value); })
      .catch(function () { loading = false; });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function render(q) {
    q = (q || '').trim().toLowerCase();
    if (!q) { results.hidden = true; results.innerHTML = ''; return; }
    if (!index) { loadIndex(); return; }
    var terms = q.split(/\s+/);
    var hits = index.filter(function (rec) {
      var hay = (rec.title + ' ' + rec.topics + ' ' + rec.date + ' ' + rec.kind + ' ' + rec.excerpt).toLowerCase();
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    }).slice(0, 25);

    if (!hits.length) {
      results.innerHTML = '<div class="search-empty">未找到匹配结果 · No matches.</div>';
      results.hidden = false;
      return;
    }
    results.innerHTML = hits.map(function (h) {
      return '<a class="search-hit" href="' + esc(h.url) + '">' +
        '<div class="sh-title">' + esc(h.title) + '</div>' +
        '<div class="sh-meta">' + esc(h.kind) + ' · ' + esc(h.date) +
        (h.topics ? ' · ' + esc(h.topics) : '') + '</div></a>';
    }).join('');
    results.hidden = false;
  }

  input.addEventListener('focus', loadIndex);
  input.addEventListener('input', function () { render(input.value); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input) { e.preventDefault(); input.focus(); }
    if (e.key === 'Escape') { results.hidden = true; }
  });
})();
"""
