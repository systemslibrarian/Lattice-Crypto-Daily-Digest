"""Central task wrapper (pyinvoke) for the lattice digest project.

Why this exists
---------------
The safe operating model is *manual, human-in-the-loop* runs. Historically those
runs were invoked by assembling raw command strings such as::

    python -m lattice_digest.workflow daily --execute --since 36h --output markdown,json --send none

Assembling that by hand (or by an LLM operator reading a Markdown runbook) is
error prone: a single dropped or added flag — ``--skip-hygiene``,
``--quality-status``, ``--run-mode`` — silently changes behavior. This module
hardcodes the blessed flag matrix so every entry point is reproducible and an
operator can run ``invoke daily-run`` instead of reconstructing the string.

Design rules
------------
* **Dry / plan by default.** ``invoke daily`` *plans*; ``invoke daily-run``
  *executes*. This mirrors the workflow command center's own default.
* **No scheduling.** These tasks never install cron / Task Scheduler entries and
  never run in the background. They are manual entry points only.
* **Single source of the flag matrix.** Callers must not re-thread flags; if a
  blessed invocation changes, it changes here.

Usage::

    pip install -e ".[dev]"     # installs invoke
    invoke --list               # show every task
    invoke ci                   # test + hygiene + diff-check (mirrors CI)
    invoke daily                # plan the daily digest (no writes)
    invoke daily-run            # execute the daily digest
    invoke backfill --date 2026-06-09
    invoke build-site
"""

from __future__ import annotations

from invoke import task

# Canonical module entry points -------------------------------------------------
WORKFLOW = "python -m lattice_digest.workflow"
RUN = "python -m lattice_digest.run"
PYTEST = "python -m pytest tests --basetemp=.pytest_tmp"


def _run(c, command: str) -> None:
    """Echo then run a command, failing the task on a non-zero exit."""
    print(f"$ {command}")
    c.run(command, pty=False, warn=False)


# --------------------------------------------------------------------------- #
# Quality gates (mirror .github/workflows/ci.yml)
# --------------------------------------------------------------------------- #


@task(help={"k": "Only run tests matching the given -k expression."})
def test(c, k=""):
    """Run the test suite the same way CI does."""
    cmd = PYTEST + (f' -k "{k}"' if k else "")
    _run(c, cmd)


@task
def hygiene(c):
    """Run release-hygiene checks."""
    _run(c, "python scripts/check_release_hygiene.py")


@task
def diff_check(c):
    """Fail on whitespace / conflict-marker errors (git diff --check)."""
    _run(c, "git diff --check")


@task
def typecheck(c, strict=False):
    """Run mypy over the typed allowlist (see mypy.ini)."""
    _run(c, "python -m mypy" + (" --strict" if strict else ""))


@task
def ci(c):
    """Full local CI gate: tests, hygiene, and whitespace/diff check."""
    test(c)
    hygiene(c)
    diff_check(c)


# --------------------------------------------------------------------------- #
# Digest workflows — PLAN (safe, no writes) vs RUN (executes)
# --------------------------------------------------------------------------- #


@task
def daily(c):
    """Plan the daily digest workflow (no network writes, no artifacts)."""
    _run(c, f"{WORKFLOW} daily")


@task(help={"since": "Lookback window (default 36h, matching GitHub Actions)."})
def daily_run(c, since="36h"):
    """Execute the daily digest with the blessed flag matrix."""
    _run(c, f"{WORKFLOW} daily --execute --since {since} --output markdown,json --send none")


@task
def weekly(c):
    """Plan the weekly research synthesis workflow."""
    _run(c, f"{WORKFLOW} weekly")


@task
def weekly_run(c, days=7, notes=False):
    """Execute the weekly research synthesis workflow."""
    extra = " --generate-notes" if notes else ""
    _run(c, f"{WORKFLOW} weekly --execute --days {days}{extra}")


@task
def full(c):
    """Plan daily followed by weekly."""
    _run(c, f"{WORKFLOW} full")


@task
def full_run(c):
    """Execute daily followed by weekly (network-heavy; acknowledged via --yes)."""
    _run(c, f"{WORKFLOW} full --execute --yes --output markdown,json --send none")


@task
def status(c):
    """Show local workflow status without writing files."""
    _run(c, f"{WORKFLOW} status")


@task(help={"strict": "Fail on warnings."})
def doctor(c, strict=False):
    """Run local environment checks without writing files."""
    _run(c, f"{WORKFLOW} doctor" + (" --strict" if strict else ""))


# --------------------------------------------------------------------------- #
# Authoritative backfill (explicit date; writes authoritative_backfill outputs)
# --------------------------------------------------------------------------- #


@task(
    help={
        "date": "Target date YYYY-MM-DD.",
        "recover": "Also retry failed sources and include latest-source feeds.",
    }
)
def backfill(c, date, recover=False):
    """Locally backfill an authoritative digest for a specific date."""
    if not date:
        raise SystemExit("backfill requires --date YYYY-MM-DD")
    extra = " --retry-failed-sources --include-latest-sources" if recover else ""
    _run(
        c,
        f"{RUN} --date {date} --output markdown,json --send none "
        f"--collector local_codex --quality-status authoritative_backfill --run-mode backfill{extra}",
    )


@task(help={"month": "Target month YYYY-MM."})
def monthly(c, month):
    """Generate the monthly lattice paper radar for a month."""
    if not month:
        raise SystemExit("monthly requires --month YYYY-MM")
    _run(c, f"python -m lattice_digest.monthly_synthesis --month {month}")


@task(help={"dry": "Plan only (do not write handoff files)."})
def handoff(c, dry=False):
    """Generate the weekly research handoff from the latest weekly JSON."""
    _run(c, "python -m lattice_digest.weekly_handoff --latest" + (" --dry-run" if dry else ""))


# --------------------------------------------------------------------------- #
# Website
# --------------------------------------------------------------------------- #


@task(help={"base_url": "Base path for project pages, e.g. /Lattice-Crypto-Daily-Digest."})
def build_site(c, output="site", base_url=""):
    """Build the public GitHub Pages website from the committed digests."""
    cmd = f"python scripts/build_site.py --output {output}"
    if base_url:
        cmd += f' --base-url "{base_url}"'
    _run(c, cmd)
