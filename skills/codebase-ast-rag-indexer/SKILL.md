---
name: codebase-ast-rag-indexer
description: AST chunking, call/type hierarchy & RAG indexer.
---

# Codebase AST, Call/Type Hierarchy & Vectorless/PagedAttention RAG Indexer

Use this skill whenever the user wants to clone/scan any **GitHub URL or local codebase** and build a complete, deterministic **AST + Symbol Relation + RAG + KV-Cache** index:

- **AST Tree Chunking (`index/chunks.jsonl`):** Exact Python AST and multi-language structural chunks (`Java`, `TypeScript`, `JavaScript`, `Go`, `Rust`, `Kotlin`, `C#`) with `chunk_id`, `parent_id`, `signature`, `docstring`, `token_count`, and `sha256` content hashes.
- **LSP/IDE-Grade Code Relations:**
  - **Call Hierarchy (`index/call_graph.json`):** Incoming callers and outgoing callees for every function/method.
  - **Type Hierarchy (`index/type_hierarchy.json`):** `super_types` (`extends` / `implements`), `sub_types`, concrete `implementations`, method **`super_implementations`** (`Child.method -> Parent.method`), and **`type_definitions`** from annotations.
  - **Cross-File References (`index/references.json`):** Every call site and inheritance reference with `file:line`.
  - **Test Traceability (`index/test_map.json`):** Automatic mapping from production classes/functions to unit tests (`direct_call` and `name_match`).
- **Four Retrieval & Inference Pipelines:**
  1. **Vectorless RAG (`index/tree_index.json` + `docs/01-TREE-INDEX-VECTORLESS-RAG.md`):** PageIndex-style hierarchical tree navigation with zero embedding drift.
  2. **Hybrid Vector + BM25 RAG (`index/chunks.jsonl` + `index/pgvector_schema.sql`):** Ready-to-run PostgreSQL `pgvector 0.8+` (`halfvec(1536)` HNSW + `tsvector` GIN) schema.
  3. **KV-Cache Prefix-Stable & PagedAttention Packing (`index/kv_paged_blocks.json` + `scripts/query_rag.py --mode kv-pack`):** Canonically orders AST chunks into fixed-size virtual token pages (`512` tokens/page, zero mid-function splits) with deterministic `prefix_hash` values for maximum Anthropic / Gemini / vLLM Automatic Prefix Caching reuse.

## Quick Commands

### 1. Index Any GitHub URL or Local Repository
```powershell
python "skills/codebase-ast-rag-indexer/scripts/ast_rag_indexer.py" `
  --repo "https://github.com/pgvector/pgvector-python" `
  --output "./rag-output" `
  --page-size 512
```

### 2. Query the Index (Vectorless RAG, Full Symbol Card, or KV-Cache Packed Context)
```powershell
# Vectorless tree-based retrieval
python "skills/codebase-ast-rag-indexer/scripts/query_rag.py" --index "./rag-output/index" --query "HalfVector" --mode vectorless

# Full IDE/LSP symbol card (definition, callers, callees, supertypes, subtypes, super_impl, refs, tests)
python "skills/codebase-ast-rag-indexer/scripts/query_rag.py" --index "./rag-output/index" --query "HalfVector" --mode symbol

# KV-Cache prefix-stable & PagedAttention-aligned prompt packet
python "skills/codebase-ast-rag-indexer/scripts/query_rag.py" --index "./rag-output/index" --query "HalfVector" --mode kv-pack
```
