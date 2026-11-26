# Codebase AST & RAG Indexer (`codebase-ast-rag-indexer`)

Use **`codebase-ast-rag-indexer`** (`scripts/ast_rag_indexer.py` & `scripts/query_rag.py`) whenever the user needs to:
- Clone and index a GitHub or local repository into AST-aware hierarchical chunks (`chunks.jsonl`) and a **Vectorless RAG Tree Index** (`tree_index.json`).
- Resolve **Call Hierarchy** (callers/callees), **Type Hierarchy** (supertypes, subtypes, implementations, super-implementations), **Definitions/Declarations**, **Type Definitions**, **References**, and **Test Traceability**.
- Pack retrieved code context into **KV-Cache prefix-stable** and **PagedAttention block-aligned** token pages or export a PostgreSQL **`pgvector`** hybrid RRF schema.