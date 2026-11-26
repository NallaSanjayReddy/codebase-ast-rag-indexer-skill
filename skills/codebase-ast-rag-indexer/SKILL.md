---
name: codebase-ast-rag-indexer
description: AST chunking, call/type hierarchy & RAG indexer.
---

# Codebase AST, Knowledge Graph, Vectorless RAG & KV-Cache/PagedAttention Indexer

Clone any GitHub URL or scan a local repository to build an IDE/LSP-grade **AST Knowledge Graph & RAG Index** with zero external dependencies (pure Python 3 stdlib).

## Synthesized Reference Architecture
- **Knowledge Graph & Traversal** (inspired by [`Graphify-Labs/graphify`](https://github.com/Graphify-Labs/graphify)): Confidence-tagged edges (`EXTRACTED`, `INFERRED`, `AMBIGUOUS`), God Nodes, zero-dependency subsystem community clustering, surprising cross-community bridges, `# WHY:` / `# NOTE:` rationale extraction, `05-GRAPH-REPORT.md`, interactive `graph.html`, plus `explain` and shortest `path` queries.
- **Dual-Embedding & Flexible Chunking** (inspired by [`OshanKHZ/bee2bee-indexer`](https://github.com/OshanKHZ/bee2bee-indexer)): `--chunk-strategy hybrid|function|class|file`, dual `nlp_text` + `code_text` payloads per chunk, and dual-vector `pgvector` HNSW schema (`nlp_embedding` + `code_embedding`).
- **Incremental Local Hybrid Search** (inspired by [`rawveg/code-rag`](https://github.com/rawveg/code-rag)): `--priority-paths`, `--exclude-dirs`, incremental SHA-256 `file_manifest.json` delta tracking, and local zero-server SQLite FTS5 BM25 search (`rag_index.sqlite`).
- **KV-Cache & PagedAttention Context Packing**: Deterministic canonical chunk sorting into fixed-size virtual token pages (`--page-size 512`) with `prefix_hash` stability and `<<<STATIC_KV_PREFIX_START>>>` / `<<<DYNAMIC_QUERY_SUFFIX>>>` prompt framing.

## Commands

### 1. Index a GitHub Repo or Local Path
```bash
python scripts/ast_rag_indexer.py \
  --repo https://github.com/pgvector/pgvector-python \
  --output ./rag_out \
  --page-size 512 \
  --chunk-strategy hybrid \
  --priority-paths pgvector \
  --incremental
```

### 2. Query the Index (6 Modes)
```bash
# Vectorless RAG tree retrieval (no embeddings)
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode vectorless

# Full IDE/LSP symbol card (definition, callers, callees, super_types, sub_types, super_impl, refs, tests)
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode symbol

# KV-Cache prefix-stable & PagedAttention-aligned prompt packet
python scripts/query_rag.py --index ./rag_out/index --query "halfvec" --mode kv-pack

# Knowledge Graph node explanation (community, degree, confidence-tagged edges, rationale)
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode explain

# Shortest path between two symbols with weakest-hop confidence
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --target "HalfVector" --mode path

# Local SQLite FTS5 BM25 + priority-path boosted search
python scripts/query_rag.py --index ./rag_out/index --query "register vector async" --mode fts
```

## Generated Artifacts
- `index/chunks.jsonl` — AST chunks with `nlp_text`, `code_text`, `kv_page_id`, `community_id`, `callers`, `callees`, `super_types`, `sub_types`, `super_implementation`, `type_definitions`, `rationale`, `tests`
- `index/graph.json` — Knowledge graph with `god_nodes`, `communities`, `surprising_bridges`, and confidence-tagged `edges`
- `index/tree_index.json` — PageIndex hierarchical tree for Vectorless RAG
- `index/call_graph.json`, `index/type_hierarchy.json`, `index/references.json`, `index/test_map.json`
- `index/kv_paged_blocks.json` — PagedAttention virtual token pages with SHA-256 `prefix_hash`
- `index/rag_index.sqlite` — Local SQLite FTS5 + BM25 search database
- `index/file_manifest.json` — SHA-256 file hashes for incremental delta indexing
- `index/pgvector_schema.sql` — PostgreSQL `pgvector` 0.8+ dual-embedding HNSW + GIN hybrid RRF schema
- `docs/00-INDEX.md` → `docs/05-GRAPH-REPORT.md` + interactive `docs/graph.html`
