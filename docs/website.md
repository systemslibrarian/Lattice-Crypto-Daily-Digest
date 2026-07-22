# Public Website (GitHub Pages)

The committed digests are published as a browsable website at:

```
https://<owner>.github.io/<repo>/
```

For this repository that is `https://systemslibrarian.github.io/Lattice-Crypto-Daily-Digest/`.

中文说明：本项目会把 `digests/` 下已提交的每日 / 每周 / 每月情报自动渲染成一个静态网站，并通过 GitHub Pages 发布。每当有新的日报被提交，网站会自动重建并更新。

## What gets published

`scripts/build_site.py` scans the committed markdown and renders a fully static
site into `site/`:

- `index.html` — landing page featuring the **latest daily digest** (paper
  counts, topics, source-health), a global search box, and recent cards for
  daily / weekly / monthly.
- `daily.html`, `weekly.html`, `monthly.html` — full archives.
- `d/<date>.html`, `w/<week>.html`, `m/<month>.html` — one page per digest with
  an auto-generated table of contents, styled tables, and prev/next navigation.
- `about.html` — coverage and methodology.
- `search-index.json` — powers instant client-side search (`/` to focus).
- `feed.xml` — RSS feed of the most recent digests.

The site supports light/dark themes and is CJK-typography aware.

## How updates flow (automatic)

1. The scheduled **Daily Lattice Crypto Digest** workflow (`.github/workflows/daily.yml`)
   generates and commits the new dated digest.
2. The **Publish Digest Website** workflow (`.github/workflows/pages.yml`) is
   chained to run after it via `workflow_run`, rebuilds `site/` from every
   committed digest, and deploys it to Pages.

It also rebuilds on direct pushes to `main` that touch `digests/**` or the
generator, and can be triggered manually from the Actions tab.

> Note: because the daily commit is made with the built-in `GITHUB_TOKEN`, the
> chained `workflow_run` trigger (not `push`) is what guarantees the site
> refreshes after each automated daily commit.

## One-time repository setup

1. Repository **Settings → Pages → Build and deployment → Source**: select
   **GitHub Actions**.
2. Ensure Actions have write access to Pages (default for `pages: write` /
   `id-token: write`, already declared in `pages.yml`).
3. Push to `main` or run **Publish Digest Website** manually once to seed the
   first deployment.

## Build it locally

```bash
python -m pip install -e ".[site]"        # installs the `markdown` extra
python scripts/build_site.py --output site
# then open site/index.html
```

For a project-pages base path (matching the live URL), pass `--base-url`:

```bash
python scripts/build_site.py --output site --base-url /Lattice-Crypto-Daily-Digest
```

If `markdown` is not installed the generator falls back to a small built-in
renderer so the build never hard-fails; installing the `site` extra produces the
best output (tables, fenced code, heading anchors).

## Notes

- `site/` is generated output and is git-ignored; it is published as a Pages
  artifact, never committed.
- Rankings and citation metadata shown on the site are advisory only — always
  verify against the primary source before deep reading.
