"""Embedding-based novelty scoring for incoming papers.

Keyword/regex ranking (``ranker.py``) computes *category* — does a paper hit the
lattice/PQC vocabulary — but not *distance*: how different an incoming abstract
is from what has already been read and approved. Two papers can hit every
keyword yet be architecturally identical; novelty is the semantic distance to
the existing corpus, which categorical matching cannot represent.

This module supplies that missing signal as an **advisory** score (it does not
replace the keyword ranker):

* An :class:`Embedder` turns text into a unit vector.
* The default :class:`HashingEmbedder` is dependency-free, deterministic, and
  offline — so it works in CI and on air-gapped machines with zero model
  downloads.
* An optional :class:`SentenceTransformerEmbedder` (``all-MiniLM-L6-v2``) is
  used when the ``[embeddings]`` extra is installed *and* opted in via the
  ``LATTICE_EMBEDDING_BACKEND`` environment variable.
* :func:`novelty_score` returns ``1 - max_cosine_similarity`` against the
  approved corpus vectors (higher = more novel).

Design constraints honoured: no heavy dependency by default, deterministic
output for tests, and no change to existing ranking behaviour.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import Protocol, runtime_checkable

DEFAULT_DIM = 256
DEFAULT_MODEL_NAME = "hashing-v1"
SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@runtime_checkable
class Embedder(Protocol):
    """Turns text into a unit-length embedding vector."""

    name: str
    dim: int

    def embed(self, text: str) -> list[float]:  # pragma: no cover - protocol
        ...


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    words = _TOKEN_RE.findall(lowered)
    grams: list[str] = list(words)
    # Character 3-grams over each word add morphological signal (e.g. "lattice"
    # vs "lattices") that plain token matching would miss.
    for word in words:
        if len(word) <= 3:
            continue
        for i in range(len(word) - 2):
            grams.append("#" + word[i : i + 3])
    return grams


def _bucket(token: str, dim: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dim


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        return vector
    return [component / norm for component in vector]


class HashingEmbedder:
    """Deterministic, dependency-free hashing bag-of-features embedder.

    Tokens and character n-grams are hashed into a fixed-width vector using
    sublinear term weighting, then L2-normalised. It captures lexical overlap
    (good enough to flag near-duplicate abstracts) without any model download.
    """

    def __init__(self, dim: int = DEFAULT_DIM, name: str = DEFAULT_MODEL_NAME) -> None:
        self.dim = dim
        self.name = name

    def embed(self, text: str) -> list[float]:
        counts: dict[int, float] = {}
        for token in _tokens(text):
            bucket = _bucket(token, self.dim)
            counts[bucket] = counts.get(bucket, 0.0) + 1.0
        vector = [0.0] * self.dim
        for bucket, count in counts.items():
            # Sublinear tf dampens repeated-term dominance.
            vector[bucket] = 1.0 + math.log(count)
        return _l2_normalize(vector)


class SentenceTransformerEmbedder:
    """Optional semantic embedder backed by sentence-transformers.

    Only constructed when the model is available; import failures are surfaced
    to the caller, which falls back to :class:`HashingEmbedder`.
    """

    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.name = f"st:{model_name}"
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        raw = self._model.encode([text], normalize_embeddings=True)[0]
        return [float(value) for value in raw]


def get_embedder() -> Embedder:
    """Return the configured embedder.

    Uses sentence-transformers only when ``LATTICE_EMBEDDING_BACKEND`` selects it
    and the package imports cleanly; otherwise the offline hashing embedder.
    """
    backend = os.environ.get("LATTICE_EMBEDDING_BACKEND", "").strip().lower()
    if backend in {"sentence-transformers", "st", "minilm"}:
        try:
            return SentenceTransformerEmbedder()
        except Exception:
            # Missing package / model download failure must not break the run.
            return HashingEmbedder()
    return HashingEmbedder()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors (0.0 if either is zero)."""
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} != {len(b)}")
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)


def max_similarity(vector: list[float], corpus: list[list[float]]) -> float:
    """Highest cosine similarity between ``vector`` and any corpus vector."""
    best = 0.0
    for candidate in corpus:
        similarity = cosine_similarity(vector, candidate)
        if similarity > best:
            best = similarity
    return best


def novelty_score(vector: list[float], corpus: list[list[float]]) -> float:
    """Novelty in ``[0, 1]``: ``1 - nearest-neighbour cosine`` vs the corpus.

    An empty corpus yields ``1.0`` (nothing to be similar to). Identical text
    yields ``0.0``.
    """
    if not corpus:
        return 1.0
    similarity = max_similarity(vector, corpus)
    return max(0.0, min(1.0, 1.0 - similarity))


def paper_text(title: str, abstract: str = "") -> str:
    """Canonical text used for embedding a paper."""
    return f"{title}\n{abstract}".strip()


def score_papers(
    db_path: Path,
    items: list[tuple[str, str]],
    *,
    embedder: Embedder | None = None,
    persist: bool = True,
) -> dict[str, float]:
    """Compute advisory novelty for ``(paper_key, text)`` items.

    Novelty is measured against the *previously stored* corpus for the chosen
    embedder (this run's papers are excluded from their own corpus), then the new
    vectors are persisted so future runs treat them as history.

    Returns ``{paper_key: novelty}`` where higher means more novel. Import is
    local to keep :mod:`lattice_digest.novelty` usable without a database.
    """
    from . import embedding_store

    model = embedder or get_embedder()
    existing = embedding_store.load_embeddings(db_path, model.name)
    new_keys = {key for key, _ in items}
    corpus = embedding_store.corpus_vectors(existing, exclude=new_keys)

    scores: dict[str, float] = {}
    to_store: list[tuple[str, list[float]]] = []
    for key, text in items:
        vector = model.embed(text)
        scores[key] = novelty_score(vector, corpus)
        to_store.append((key, vector))

    if persist and to_store:
        embedding_store.store_embeddings(db_path, model.name, to_store)
    return scores
