# Codebase AST, Dual Vector + Vectorless RAG Indexer Skill (`v3.0`)

<p align="center">
  <img src="./assets/logo.svg" alt="Codebase AST & RAG Indexer" width="120" />
</p>

An open-source, zero-dependency agent skill (for **Antigravity**, **Claude Code**, **Codex**, and **Gemini CLI**) that clones any GitHub repository (or scans a local codebase) and builds **BOTH Vectorless RAG** (AST Tree + Confidence-Tagged Knowledge Graph) **AND Vector-Based RAG** (Dual NLP + Code Embeddings, SQLite FTS5 + Vector Store, Qdrant Points, PostgreSQL `pgvector` HNSW Schema, and Hybrid Reciprocal Rank Fusion) with **KV-Cache / PagedAttention** block packing.

## Dual RAG Architecture (Vectorless + Vector + Hybrid RRF)

| Capability | Vectorless RAG (`Graphify-Labs/graphify` inspired) | Vector-Based RAG (`rawveg/code-rag` + `bee2bee-indexer` inspired) |
| :--- | :--- | :--- |
| **Index Artifacts** | `tree_index.json`, `graph.json`, `call_graph.json`, `type_hierarchy.json`, `05-GRAPH-REPORT.md`, interactive `graph.html` | `vectors.jsonl`, `vector_meta.json`, `qdrant_points.jsonl`, `rag_index.sqlite` (`chunk_vectors` + `chunks_fts`), `pgvector_schema.sql` |
| **Retrieval Modes** | `--mode vectorless` (Tree + 1-hop Graph subgraph), `--mode explain`, `--mode path`, `--mode symbol` | `--mode vector` (Dual NLP + Code cosine similarity), `--mode fts` (SQLite FTS5 BM25), `--mode hybrid` (**RRF** fusing Vector + FTS5 + Graph) |
| **Embedding Providers** | Zero embeddings required (`--rag-mode vectorless`) | Pluggable: offline zero-dep `tfidf` (default, `D=128`), `sentence-transformers` (`all-MiniLM-L6-v2`), `openai`, `ollama` |
| **Accuracy & Graph Hygiene** | Same-language-family + import-constrained call edges (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`), **production-isolated communities** (tests never hijack prod subsystems), **import cycle detection**, `# WHY:`/`# NOTE:` rationale nodes | Dual `nlp_text` + `code_text` embeddings, `--priority-paths` boost, incremental SHA-256 `file_manifest.json` delta tracking |
| **LLM Inference Packing** | Canonical **KV-Cache prefix-stable** & **PagedAttention** 512-token virtual pages (`kv_paged_blocks.json`, `--mode kv-pack`) | Same KV-page coordinates stored in SQLite, Qdrant payload, and `pgvector` table for prefix-stable prompt packing |

## Quick Start

```bash
# 1. Build BOTH Vectorless + Vector RAG indexes (zero external dependencies)
python skills/codebase-ast-rag-indexer/scripts/ast_rag_indexer.py \
  --repo https://github.com/pgvector/pgvector-python \
  --output ./examples/pgvector-python-rag-index \
  --rag-mode both \
  --embedding-provider tfidf \
  --page-size 512 \
  --priority-paths pgvector \
  --incremental

# 2. Hybrid RRF (Vector Cosine + SQLite FTS5 BM25 + Graph Centrality)
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "async vector registration" --mode hybrid

# 3. Pure Vector Search (Dual NLP + Code cosine similarity)
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "register halfvec psycopg" --mode vector

# 4. Pure Vectorless Tree + 1-Hop Knowledge Graph Subgraph
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "Vector" --mode vectorless

# 5. Graph Explain & Shortest Path (with weakest-hop confidence)
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "pgvector.vector.Vector" --mode explain

python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "pgvector.vector.Vector" --target "pgvector.halfvec.HalfVector" --mode path
```

## Included Public Open-Source Example (`pgvector/pgvector-python`)
- [`examples/pgvector-python-rag-index/docs/00-INDEX.md`](./examples/pgvector-python-rag-index/docs/00-INDEX.md)
- [`examples/pgvector-python-rag-index/docs/05-GRAPH-REPORT.md`](./examples/pgvector-python-rag-index/docs/05-GRAPH-REPORT.md)
- [`examples/pgvector-python-rag-index/docs/graph.html`](./examples/pgvector-python-rag-index/docs/graph.html)

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Keywords & Topics
`rag` `vectorless-rag` `graph-rag` `hybrid-search` `ast` `code-indexing` `knowledge-graph` `call-hierarchy` `type-hierarchy` `kv-cache` `paged-attention` `pgvector` `qdrant` `sqlite-fts5` `bm25` `rrf` `agent-skills` `claude-code` `antigravity` `codex`

## License
MIT License — see [LICENSE](./LICENSE).
