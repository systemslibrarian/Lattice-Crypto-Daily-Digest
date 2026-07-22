# Embedding-based Novelty Scoring

Keyword ranking (`ranker.py`) answers *"is this a lattice/PQC paper?"* — a
**category**. It cannot answer *"how different is this from what I've already
read?"* — a **distance**. Two papers can hit every keyword yet be architecturally
identical. Novelty is the semantic distance between an incoming abstract and the
corpus of previously seen papers.

中文说明：关键词排序只能判断“是不是格密码/PQC 论文”（类别），无法衡量“和已读文献相比有多新”（距离）。本模块用向量嵌入 + 余弦相似度补上这个信号，作为**建议性**分数，不改变现有排序结果。

## What it provides

- `lattice_digest.novelty` — an `Embedder` abstraction, cosine similarity, and
  `novelty_score(vector, corpus) = 1 - nearest-neighbour cosine` (higher = more
  novel; empty corpus = fully novel; identical text = `0.0`).
- `lattice_digest.embedding_store` — a persistent `paper_embeddings` table in
  `papers.db` that **accumulates across runs** (unlike the `papers` table, which
  is rewritten each run), so it serves as the historical reference corpus.
- `novelty.score_papers(db_path, items)` — the orchestration entry point:
  scores `(paper_key, text)` items against the stored corpus (this run's papers
  are excluded from their own corpus), then persists the new vectors.

## Backends (offline by default)

| Backend | Dependency | When used |
| --- | --- | --- |
| `HashingEmbedder` (default) | none | Always, unless a semantic backend is opted in. Deterministic, offline, CI-safe. |
| `SentenceTransformerEmbedder` (`all-MiniLM-L6-v2`) | `[embeddings]` extra | Only when `LATTICE_EMBEDDING_BACKEND=sentence-transformers` **and** the package imports. Falls back to hashing on any failure. |

The hashing embedder hashes tokens and character 3-grams into a fixed-width,
L2-normalised vector with sublinear term weighting. It captures lexical overlap
well enough to flag near-duplicate abstracts with **zero model download**, which
keeps the core project dependency-free and runnable air-gapped.

To enable the semantic backend:

```bash
python -m pip install -e ".[embeddings]"
export LATTICE_EMBEDDING_BACKEND=sentence-transformers   # PowerShell: $env:LATTICE_EMBEDDING_BACKEND="sentence-transformers"
```

## Design choices

- **Advisory, not a ranker replacement.** Novelty is exposed as a separate score
  and does not alter existing keyword ranking output. This preserves the golden
  ranking tests and lets novelty be adopted incrementally.
- **Deterministic default.** The hashing embedder produces identical vectors for
  identical text, so tests and CI stay reproducible.
- **Model tagging.** Embeddings are stored per `model` name, so switching
  backends never mixes incompatible vector spaces.
