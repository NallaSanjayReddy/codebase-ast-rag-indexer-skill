---
name: codebase-ast-rag-indexer
description: AST chunking, call/type hierarchy & RAG indexer.
---

# Codebase AST, Dual Vector + Vectorless RAG & KV-Cache/PagedAttention Indexer (`v3.0`)

Clone any GitHub URL or scan a local repository to generate **BOTH Vectorless RAG** (PageIndex tree + confidence-tagged Knowledge Graph) **AND Vector-Based RAG** (real dual NLP + Code embeddings, SQLite FTS5 + Vector store, Qdrant points, `pgvector` HNSW schema, and Hybrid RRF retrieval) with zero external dependencies by default.

## Supported RAG Modes (`--rag-mode`)
- **`both` (default):** Generates complete Vectorless RAG (`tree_index.json`, `graph.json`, `graph.html`) AND Vector RAG (`vectors.jsonl`, `vector_meta.json`, `qdrant_points.jsonl`, `rag_index.sqlite` FTS5 + vectors, `pgvector_schema.sql`).
- **`vectorless`:** Zero-embedding AST Tree + Knowledge Graph (inspired by `Graphify-Labs/graphify`).
- **`vector`:** Dual NLP + Code embeddings via `--embedding-provider tfidf|sentence-transformers|openai|ollama` (inspired by `rawveg/code-rag` and `OshanKHZ/bee2bee-indexer`).

## Commands

### 1. Index a GitHub Repo or Local Path
```bash
python scripts/ast_rag_indexer.py \
  --repo https://github.com/pgvector/pgvector-python \
  --output ./rag_out \
  --rag-mode both \
  --embedding-provider tfidf \
  --page-size 512 \
  --chunk-strategy hybrid \
  --priority-paths pgvector \
  --incremental
```

### 2. Query the Index (8 Modes)
```bash
# Hybrid RRF (Vector Cosine + SQLite FTS5 BM25 + Knowledge Graph degree)
python scripts/query_rag.py --index ./rag_out/index --query "async vector registration" --mode hybrid

# Pure Vector RAG (dual nlp_vector + code_vector cosine similarity)
python scripts/query_rag.py --index ./rag_out/index --query "register halfvec psycopg" --mode vector

# Vectorless RAG (PageIndex tree + 1-hop Knowledge Graph subgraph with confidence tags)
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode vectorless

# Local SQLite FTS5 BM25 + priority-path search
python scripts/query_rag.py --index ./rag_out/index --query "register vector async" --mode fts

# Knowledge Graph explain & shortest path (with weakest-hop confidence)
python scripts/query_rag.py --index ./rag_out/index --query "pgvector.vector.Vector" --mode explain
python scripts/query_rag.py --index ./rag_out/index --query "pgvector.vector.Vector" --target "pgvector.halfvec.HalfVector" --mode path

# IDE/LSP symbol card & KV-Cache PagedAttention prompt packer
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode symbol
python scripts/query_rag.py --index ./rag_out/index --query "Vector" --mode kv-pack
```
