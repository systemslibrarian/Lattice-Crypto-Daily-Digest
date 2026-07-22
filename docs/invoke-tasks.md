# Task Runner (`invoke`)

`tasks.py` centralizes every blessed command invocation behind [pyinvoke](https://www.pyinvoke.org/)
so runs are reproducible and no operator (human or LLM) has to hand-assemble
`python -m lattice_digest.run …` strings — the exact failure mode where a dropped
or added flag (`--skip-hygiene`, `--quality-status`, `--run-mode`) silently
changes behavior.

中文说明：`tasks.py` 用 `invoke` 把所有既定命令的参数矩阵固化下来。操作者只需运行 `invoke daily-run`，不用手动拼接 `python -m lattice_digest.run ...`，避免误加/漏掉参数。它只提供手动入口，不安装任何计划任务，也不在后台运行。

## Setup

```bash
python -m pip install -e ".[dev]"   # installs invoke
invoke --list                       # see every task
```

## Safety model

- **Plan by default, execute explicitly.** `invoke daily` *plans* (no writes);
  `invoke daily-run` *executes*. Same for `weekly` / `weekly-run`,
  `full` / `full-run`.
- **No scheduling, no background.** These tasks never install cron / Windows Task
  Scheduler entries. They are manual entry points only, consistent with the
  project's manual-only operating rules.
- **Single source of the flag matrix.** If a blessed invocation changes, it
  changes in `tasks.py` — callers never re-thread flags.

## Common tasks

| Command | What it does |
| --- | --- |
| `invoke ci` | Tests + release hygiene + `git diff --check` (mirrors CI) |
| `invoke test -k <expr>` | Run the test suite (optionally filtered) |
| `invoke typecheck` | Run mypy over the typed allowlist |
| `invoke daily` / `invoke daily-run` | Plan / execute the daily digest |
| `invoke weekly` / `invoke weekly-run` | Plan / execute the weekly synthesis |
| `invoke full` / `invoke full-run` | Plan / execute daily then weekly |
| `invoke backfill --date 2026-06-09` | Authoritative local backfill for a date |
| `invoke backfill --date 2026-06-09 --recover` | …also retry failed / latest sources |
| `invoke monthly --month 2026-06` | Monthly lattice paper radar |
| `invoke handoff` / `invoke handoff --dry` | Weekly research handoff from latest weekly JSON |
| `invoke status` / `invoke doctor` | Local status / environment checks (no writes) |
| `invoke build-site` | Build the public GitHub Pages website |

Run `invoke <task> --help` for per-task options.
