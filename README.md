# Codebase AST, Knowledge Graph & Dual Vector/Vectorless RAG Indexer Skill (`v3.0`)

<p align="center">
  <img src="./assets/logo.svg" alt="Codebase AST & RAG Indexer" width="120" />
</p>

An open-source, zero-dependency agent skill (for **Antigravity**, **Claude Code**, **Codex**, and **Gemini CLI**) that clones any GitHub repository (or scans a local codebase) and builds **BOTH Vectorless RAG** (AST Tree + Confidence-Tagged Knowledge Graph) **AND Vector-Based RAG** (Dual NLP + Code Embeddings, SQLite FTS5 + Vector Store, Qdrant Points, PostgreSQL `pgvector` HNSW Schema, and Hybrid Reciprocal Rank Fusion) with **KV-Cache / PagedAttention** block packing.

---

## Architecture Overview

```mermaid
flowchart LR
    Repo["GitHub URL or Local Repo"] --> AST["AST & Structural Parser<br/>(Python, Java, TS/JS, Go, Rust, Kotlin, C#, PHP)"]
    AST --> VL["Vectorless RAG<br/>tree_index.json + graph.json + graph.html"]
    AST --> VEC["Vector-Based RAG<br/>Dual NLP + Code Embeddings<br/>vectors.jsonl + SQLite FTS5 + Qdrant + pgvector"]
    AST --> KV["KV-Cache & PagedAttention<br/>512-tok canonical pages + prefix_hash"]
    VL --> Q["query_rag.py (8 Modes)<br/>hybrid | vector | vectorless | fts<br/>explain | path | symbol | kv-pack"]
    VEC --> Q
    KV --> Q
```

## Dual RAG Capabilities (Vectorless + Vector + Hybrid RRF)

| Capability | Vectorless RAG (Zero Embeddings) | Vector-Based RAG (Dual Embeddings + Hybrid) |
| :--- | :--- | :--- |
| **Index Artifacts** | `tree_index.json`, `graph.json`, `call_graph.json`, `type_hierarchy.json`, `05-GRAPH-REPORT.md`, interactive `graph.html` | `vectors.jsonl`, `vector_meta.json`, `qdrant_points.jsonl`, `rag_index.sqlite` (`chunk_vectors` + `chunks_fts`), `pgvector_schema.sql` |
| **Retrieval Modes** | `--mode vectorless` (Tree + 1-hop Graph subgraph), `--mode explain`, `--mode path`, `--mode symbol` | `--mode vector` (Dual NLP + Code cosine similarity), `--mode fts` (SQLite FTS5 BM25), `--mode hybrid` (**RRF** fusing Vector + FTS5 + Graph) |
| **Embedding Providers** | Zero embeddings required (`--rag-mode vectorless`) | Pluggable: offline zero-dep `tfidf` (default, `D=128`), `sentence-transformers` (`all-MiniLM-L6-v2`), `openai`, `ollama` |
| **Graph & Symbol Hygiene** | Same-language-family + import-constrained call edges (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`), production-isolated subsystem communities, import cycle detection, `# WHY:` / `# NOTE:` rationale nodes | Dual `nlp_text` + `code_text` embeddings, `--priority-paths` relevance boost, incremental SHA-256 `file_manifest.json` delta tracking |
| **LLM Inference Packing** | Canonical **KV-Cache prefix-stable** & **PagedAttention** 512-token virtual pages (`kv_paged_blocks.json`, `--mode kv-pack`) | Same KV-page coordinates stored in SQLite, Qdrant payload, and `pgvector` table for prefix-stable prompt packing |

---

## Quick Start

### 1. Index Any GitHub Repository or Local Path

```bash
python skills/codebase-ast-rag-indexer/scripts/ast_rag_indexer.py \
  --repo https://github.com/pgvector/pgvector-python \
  --output ./examples/pgvector-python-rag-index \
  --rag-mode both \
  --embedding-provider tfidf \
  --page-size 512 \
  --priority-paths pgvector \
  --incremental
```

**Sample Output:**
```text
SUCCESS: Indexed 74 files -> 675 AST chunks, 675 dual vectors (tfidf d=128), 2491 graph edges (15 communities), 124 KV pages
```

You can also run **Vectorless-only** (`--rag-mode vectorless`), switch chunk granularity (`--chunk-strategy hybrid|function|class|file`), or swap in neural embeddings (`--embedding-provider sentence-transformers`, `openai`, or `ollama`).

---

## Real Query Examples (8 Retrieval Modes)

All examples below are captured from running `query_rag.py` against the included [`examples/pgvector-python-rag-index/`](./examples/pgvector-python-rag-index/docs/00-INDEX.md) index.

### Example 1 — Hybrid Reciprocal Rank Fusion (`--mode hybrid`)
Fuses **Vector Cosine Rank + SQLite FTS5 BM25 Rank + Knowledge Graph Degree** into a single ranked result:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "async psycopg register vector" \
  --mode hybrid --top-k 3
```

```json
{
  "mode": "hybrid_rrf",
  "query": "async psycopg register vector",
  "results": [
    {
      "chunk_id": "pgvector.psycopg.register.register_vector_async",
      "kind": "function",
      "community": "pgvector/psycopg",
      "kv_page_id": 22,
      "degree": 12,
      "vector_rank": 2,
      "fts_rank": 1,
      "rrf_score": 0.037652
    },
    {
      "chunk_id": "pgvector.psycopg.vector.register_vector_info",
      "kind": "function",
      "community": "pgvector/psycopg",
      "kv_page_id": 24,
      "degree": 5,
      "vector_rank": 4,
      "fts_rank": 5,
      "rrf_score": 0.034593
    }
  ]
}
```

### Example 2 — Pure Vector Search (`--mode vector`)
Blends dual `nlp_vector` (0.6 weight) and `code_vector` (0.4 weight) cosine similarity with `--priority-paths` boost:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "async psycopg register vector" \
  --mode vector --top-k 2
```

```json
{
  "mode": "vector",
  "query": "async psycopg register vector",
  "results": [
    {
      "chunk_id": "pgvector.psycopg2.vector.register_vector_info",
      "file": "pgvector/psycopg2/vector.py",
      "community": "pgvector/psycopg",
      "kv_page_id": 27,
      "nlp_cosine": 0.8358,
      "code_cosine": 0.4117,
      "score": 1.3323
    },
    {
      "chunk_id": "pgvector.psycopg.register.register_vector_async",
      "file": "pgvector/psycopg/register.py",
      "community": "pgvector/psycopg",
      "kv_page_id": 22,
      "nlp_cosine": 0.8745,
      "code_cosine": 0.2921,
      "score": 1.2831
    }
  ]
}
```

### Example 3 — Vectorless RAG: Tree + 1-Hop Knowledge Graph (`--mode vectorless`)
Zero embeddings required — retrieves matching AST nodes plus their 1-hop confidence-tagged graph neighborhood and linked unit tests:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "HalfVector" \
  --mode vectorless --top-k 2
```

```markdown
# Vectorless Tree + 1-Hop Graph Subgraph for: 'HalfVector'

- **pgvector.django.halfvec.HalfVectorField** (`class` @ `pgvector/django/halfvec.py:8-47` | KV-Page `6` | Comm `pgvector/django` | deg=`2`)
  - Signature: `class HalfVectorField(Field):`
  - Graph 1-hop: `<-- tests.test_django.TestDjango.test_half_precision` [`calls` | `EXTRACTED`]
  - Graph 1-hop: `<-- tests.test_django.TestDjango.test_half_precision` [`tests` | `EXTRACTED`]
  - Tests (1): tests.test_django.TestDjango.test_half_precision
```

### Example 4 — Symbol Neighborhood Explanation (`--mode explain`)
Inspects a symbol's source file, KV-Page, production subsystem community, degree, and confidence-tagged incoming/outgoing edges:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "pgvector.vector.Vector" \
  --mode explain
```

```text
Node: pgvector.vector.Vector
  Source:    pgvector/vector.py:12 (KV-Page 40)
  Community: #1 (pgvector/psycopg)
  Degree:    154
  Signature: class Vector:

Incoming Connections (154):
  <-- pgvector.asyncpg.register.register_vector [calls] [EXTRACTED]
  <-- pgvector.django.functions.DistanceBase.__init__ [calls] [EXTRACTED]
  <-- pgvector.psycopg.vector.VectorDumper.dump [calls] [EXTRACTED]
  ...
```

### Example 5 — Shortest Path Between Two Symbols (`--mode path`)
Finds the shortest graph path between any two symbols and computes overall path confidence from its weakest hop:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "pgvector.vector.Vector" \
  --target "pgvector.halfvec.HalfVector" \
  --mode path
```

```text
Shortest path (2 hops) | Overall confidence (weakest hop): [EXTRACTED]
pgvector.vector.Vector <--[calls|EXTRACTED]<-- pgvector.asyncpg.register.register_vector -->[calls|EXTRACTED]--> pgvector.halfvec.HalfVector
```

### Example 6 — KV-Cache Prefix-Stable & PagedAttention Prompt Packet (`--mode kv-pack`)
Orders retrieved chunks deterministically by `(kv_page_id, kv_token_offset)` inside a static prefix block so LLM inference engines (vLLM, SGLang, Anthropic/OpenAI prompt caching) maximize KV-cache prefix reuse:

```bash
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "register_vector_async" \
  --mode kv-pack --top-k 2
```

```text
<<<STATIC_KV_PREFIX_START>>>
# PagedAttention Block Table: pages=[22] | total_chunks=1

## [KV-Page 22 | offset=0 | sha256=8f14e45fceea167a | comm=pgvector/psycopg] pgvector.psycopg.register.register_vector_async
# File: pgvector/psycopg/register.py:26-39 | SuperImpl: None | Tests: ['tests.test_psycopg.TestPsycopg.test_async']
async def register_vector_async(context):
    ...

<<<STATIC_KV_PREFIX_END>>>
<<<DYNAMIC_QUERY_SUFFIX>>>
User Query: register_vector_async
```

---

## Included Generated Example Output

Browse the complete generated index and interactive knowledge graph for `pgvector/pgvector-python`:
- [`examples/pgvector-python-rag-index/docs/00-INDEX.md`](./examples/pgvector-python-rag-index/docs/00-INDEX.md) — Executive metrics & index map
- [`examples/pgvector-python-rag-index/docs/01-TREE-INDEX-VECTORLESS-RAG.md`](./examples/pgvector-python-rag-index/docs/01-TREE-INDEX-VECTORLESS-RAG.md) — Hierarchical Vectorless RAG tree
- [`examples/pgvector-python-rag-index/docs/02-CALL-AND-TYPE-HIERARCHY.md`](./examples/pgvector-python-rag-index/docs/02-CALL-AND-TYPE-HIERARCHY.md) — Supertypes, subtypes & method overrides
- [`examples/pgvector-python-rag-index/docs/03-REFERENCES-AND-TESTS-MAP.md`](./examples/pgvector-python-rag-index/docs/03-REFERENCES-AND-TESTS-MAP.md) — Cross-file references & test traceability
- [`examples/pgvector-python-rag-index/docs/04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./examples/pgvector-python-rag-index/docs/04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md) — PagedAttention virtual token pages & prefix hashes
- [`examples/pgvector-python-rag-index/docs/05-GRAPH-REPORT.md`](./examples/pgvector-python-rag-index/docs/05-GRAPH-REPORT.md) — God Nodes, subsystem communities, cross-community bridges & import cycles
- [`examples/pgvector-python-rag-index/docs/graph.html`](./examples/pgvector-python-rag-index/docs/graph.html) — Self-contained interactive force-directed graph explorer

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Keywords & Topics
`rag` `vectorless-rag` `graph-rag` `hybrid-search` `ast` `code-indexing` `knowledge-graph` `call-hierarchy` `type-hierarchy` `kv-cache` `paged-attention` `pgvector` `qdrant` `sqlite-fts5` `bm25` `rrf` `agent-skills` `claude-code` `antigravity` `codex`

## License
MIT License — see [LICENSE](./LICENSE).
