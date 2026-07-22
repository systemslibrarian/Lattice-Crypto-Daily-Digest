"""Persistent storage of paper embeddings in ``papers.db``.

Kept separate from :func:`lattice_digest.storage.write_sqlite` (which rewrites
the ``papers`` table wholesale each run) so the embedding corpus *accumulates*
across runs and can serve as the "historically seen" reference set for novelty
scoring.

The table is intentionally minimal and self-managing::

    paper_embeddings(paper_key, model, dim, vector_json, updated_at)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_CREATE = """
CREATE TABLE IF NOT EXISTS paper_embeddings (
    paper_key TEXT NOT NULL,
    model TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (paper_key, model)
)
"""


def ensure_table(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_CREATE)
        conn.commit()
    finally:
        conn.close()


def store_embeddings(
    db_path: Path,
    model: str,
    items: list[tuple[str, list[float]]],
    *,
    now: datetime | None = None,
) -> int:
    """Upsert ``(paper_key, vector)`` pairs for a model. Returns count written."""
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    conn = sqlite3.connect(db_path)
    written = 0
    try:
        conn.execute(_CREATE)
        for paper_key, vector in items:
            conn.execute(
                """
                INSERT INTO paper_embeddings (paper_key, model, dim, vector_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(paper_key, model) DO UPDATE SET
                    dim=excluded.dim,
                    vector_json=excluded.vector_json,
                    updated_at=excluded.updated_at
                """,
                (paper_key, model, len(vector), json.dumps(vector), stamp),
            )
            written += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return written


def load_embeddings(db_path: Path, model: str) -> dict[str, list[float]]:
    """Return ``{paper_key: vector}`` for a model (empty if table/rows absent)."""
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    try:
        try:
            rows = conn.execute(
                "SELECT paper_key, vector_json FROM paper_embeddings WHERE model = ?",
                (model,),
            ).fetchall()
        except sqlite3.OperationalError:
            return {}
        result: dict[str, list[float]] = {}
        for paper_key, vector_json in rows:
            try:
                result[str(paper_key)] = [float(v) for v in json.loads(vector_json)]
            except (ValueError, TypeError):
                continue
        return result
    finally:
        conn.close()


def corpus_vectors(embeddings: dict[str, list[float]], exclude: set[str] | None = None) -> list[list[float]]:
    """Corpus list for novelty scoring, optionally excluding given paper keys."""
    skip = exclude or set()
    return [vector for key, vector in embeddings.items() if key not in skip]
