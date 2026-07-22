from __future__ import annotations

from pathlib import Path

from lattice_digest import embedding_store
from lattice_digest.novelty import (
    HashingEmbedder,
    cosine_similarity,
    get_embedder,
    novelty_score,
    paper_text,
    score_papers,
)

LWE_A = "Efficient LWE secret recovery leveraging low Hamming weight hints"
LWE_B = "Recovering LWE secrets efficiently using low Hamming weight hint leakage"
UNRELATED = "A survey of oriented elliptic curve isogeny problems for signatures"


def test_hashing_embedder_is_deterministic() -> None:
    e = HashingEmbedder()
    assert e.embed(LWE_A) == e.embed(LWE_A)
    assert len(e.embed(LWE_A)) == e.dim


def test_embedding_is_unit_length() -> None:
    vec = HashingEmbedder().embed(LWE_A)
    norm = sum(v * v for v in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_cosine_bounds_and_identity() -> None:
    e = HashingEmbedder()
    v = e.embed(LWE_A)
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9
    sim = cosine_similarity(e.embed(LWE_A), e.embed(UNRELATED))
    assert 0.0 <= sim < 1.0


def test_similar_papers_are_less_novel_than_unrelated() -> None:
    e = HashingEmbedder()
    corpus = [e.embed(LWE_A)]
    near = novelty_score(e.embed(LWE_B), corpus)
    far = novelty_score(e.embed(UNRELATED), corpus)
    assert near < far, f"paraphrase novelty {near} should be < unrelated novelty {far}"


def test_identical_text_has_zero_novelty_and_empty_corpus_is_fully_novel() -> None:
    e = HashingEmbedder()
    corpus = [e.embed(LWE_A)]
    assert novelty_score(e.embed(LWE_A), corpus) == 0.0
    assert novelty_score(e.embed(LWE_A), []) == 1.0


def test_default_embedder_is_offline_hashing() -> None:
    # Without opting in, we must get the dependency-free deterministic backend.
    assert isinstance(get_embedder(), HashingEmbedder)


def test_embedding_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "papers.db"
    e = HashingEmbedder()
    items = [("key-a", e.embed(LWE_A)), ("key-b", e.embed(UNRELATED))]
    written = embedding_store.store_embeddings(db, e.name, items)
    assert written == 2

    loaded = embedding_store.load_embeddings(db, e.name)
    assert set(loaded) == {"key-a", "key-b"}
    assert loaded["key-a"] == e.embed(LWE_A)

    # Excluding the paper itself yields the historical corpus for novelty.
    corpus = embedding_store.corpus_vectors(loaded, exclude={"key-a"})
    assert corpus == [loaded["key-b"]]


def test_load_missing_db_or_model_is_empty(tmp_path: Path) -> None:
    assert embedding_store.load_embeddings(tmp_path / "nope.db", "hashing-v1") == {}
    db = tmp_path / "papers.db"
    embedding_store.ensure_table(db)
    assert embedding_store.load_embeddings(db, "unknown-model") == {}


def test_score_papers_first_run_all_novel_then_corpus_accumulates(tmp_path: Path) -> None:
    db = tmp_path / "papers.db"
    e = HashingEmbedder()

    # First run: empty history -> every paper is fully novel, and vectors persist.
    first = score_papers(db, [("p1", LWE_A)], embedder=e)
    assert first["p1"] == 1.0

    # Second run: a near-paraphrase of p1 is now recognisably un-novel because p1
    # is in the stored corpus; an unrelated paper stays highly novel.
    second = score_papers(db, [("p2", LWE_B), ("p3", UNRELATED)], embedder=e)
    assert second["p2"] < second["p3"]
    assert second["p2"] < 1.0


def test_score_papers_excludes_same_run_papers_from_corpus(tmp_path: Path) -> None:
    db = tmp_path / "papers.db"
    e = HashingEmbedder()
    # Two near-duplicate papers submitted together must not cancel each other's
    # novelty within the same run (corpus excludes this run's keys).
    scores = score_papers(db, [("a", LWE_A), ("b", LWE_B)], embedder=e)
    assert scores["a"] == 1.0 and scores["b"] == 1.0


def test_paper_text_combines_title_and_abstract() -> None:
    assert paper_text("Title", "Abstract") == "Title\nAbstract"
    assert paper_text("Title", "") == "Title"
