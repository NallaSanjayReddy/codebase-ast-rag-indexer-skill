# Codebase AST, Knowledge Graph & RAG Indexer Skill (`v2.0`)

<p align="center">
  <img src="./assets/logo.svg" alt="Codebase AST & RAG Indexer" width="120" />
</p>

An open-source, zero-dependency agent skill (for **Antigravity**, **Claude Code**, **Codex**, and **Gemini CLI**) that clones any GitHub repository (or scans a local codebase) and builds a complete **AST + LSP Symbol Hierarchy + Knowledge Graph + Vectorless RAG + SQLite FTS5 + Dual-Embedding `pgvector` + KV-Cache / PagedAttention** index.

## Architectural Inspirations & Reference Synthesis

This repository synthesizes the strongest architectural patterns from three open-source code indexing systems into a single zero-dependency pipeline:

| Reference Project | Patterns Adopted in `codebase-ast-rag-indexer` |
| :--- | :--- |
| **[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)** | Confidence-tagged knowledge graph (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`), builtin-filtered **God Nodes**, subsystem community detection, **surprising cross-community bridges**, `# WHY:` / `# NOTE:` rationale extraction, `05-GRAPH-REPORT.md`, self-contained interactive **`graph.html`**, plus `--mode explain` and shortest `--mode path` traversal with weakest-hop confidence. |
| **[OshanKHZ/bee2bee-indexer](https://github.com/OshanKHZ/bee2bee-indexer)** | Flexible AST chunking strategies (`--chunk-strategy hybrid\|function\|class\|file`), `--output-format full\|chunks\|metadata`, and **dual-representation payloads** (`nlp_text` + `code_text`) paired with dual HNSW columns (`nlp_embedding` + `code_embedding`) in `pgvector_schema.sql`. |
| **[rawveg/code-rag](https://github.com/rawveg/code-rag)** | Priority directory boosting (`--priority-paths`), configurable exclusions (`--exclude-dirs`), incremental SHA-256 `file_manifest.json` delta tracking (`--incremental`), and a local zero-server **SQLite FTS5 BM25** hybrid search database (`rag_index.sqlite`). |

## Core Capabilities

1. **AST-Aware Hierarchical Chunking (`chunks.jsonl`)** — Extracts classes, interfaces, structs, traits, functions, and methods with exact line ranges, signatures, docstrings, `# WHY:` / `# NOTE:` rationale comments, and dual `nlp_text` + `code_text` representations.
2. **IDE / LSP-Grade Symbol Context** — Resolves bidirectional **Call Hierarchy** (`callers`/`callees`), **Type Hierarchy** (`super_types`, `sub_types`, `implementations`, `super_implementations`), **Type Definitions**, **Cross-File References**, and **Production-to-Test Traceability**.
3. **Knowledge Graph & Interactive Explorer (`graph.json`, `05-GRAPH-REPORT.md`, `graph.html`)** — Computes degree-ranked God Nodes, subsystem communities, and cross-community bridges; renders an interactive HTML5 Canvas force-directed graph.
4. **Vectorless RAG (`tree_index.json`) & Local Hybrid FTS5 (`rag_index.sqlite`)** — Query immediately without embeddings or external servers via `--mode vectorless`, `--mode explain`, `--mode path`, `--mode symbol`, or `--mode fts`.
5. **KV-Cache Prefix Stability & PagedAttention Block Allocation (`kv_paged_blocks.json`)** — Deterministically sorts symbols into fixed-size virtual token pages (`--page-size 512`) with SHA-256 `prefix_hash` and emits `<<<STATIC_KV_PREFIX_START>>>` / `<<<DYNAMIC_QUERY_SUFFIX>>>` prompt packets (`--mode kv-pack`).

## Quick Start

```bash
# 1. Clone & index any GitHub repo (zero external dependencies)
python skills/codebase-ast-rag-indexer/scripts/ast_rag_indexer.py \
  --repo https://github.com/pgvector/pgvector-python \
  --output ./examples/pgvector-python-rag-index \
  --page-size 512 \
  --chunk-strategy hybrid \
  --priority-paths pgvector \
  --incremental

# 2. Query: Explain a symbol with confidence-tagged graph edges
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "Vector" --mode explain

# 3. Query: Shortest path between two symbols (with weakest-hop confidence)
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "Vector" --target "HalfVector" --mode path

# 4. Query: Local SQLite FTS5 BM25 + priority-path boosted search
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "register vector async" --mode fts

# 5. Query: KV-Cache prefix-stable & PagedAttention-aligned context packet
python skills/codebase-ast-rag-indexer/scripts/query_rag.py \
  --index ./examples/pgvector-python-rag-index/index \
  --query "Vector" --mode kv-pack
```

## Included Public Open-Source Example

- **[`examples/pgvector-python-rag-index/docs/00-INDEX.md`](./examples/pgvector-python-rag-index/docs/00-INDEX.md)** — Live index of [`pgvector/pgvector-python`](https://github.com/pgvector/pgvector-python) including:
  - [`01-TREE-INDEX-VECTORLESS-RAG.md`](./examples/pgvector-python-rag-index/docs/01-TREE-INDEX-VECTORLESS-RAG.md)
  - [`02-CALL-AND-TYPE-HIERARCHY.md`](./examples/pgvector-python-rag-index/docs/02-CALL-AND-TYPE-HIERARCHY.md)
  - [`03-REFERENCES-AND-TESTS-MAP.md`](./examples/pgvector-python-rag-index/docs/03-REFERENCES-AND-TESTS-MAP.md)
  - [`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./examples/pgvector-python-rag-index/docs/04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)
  - [`05-GRAPH-REPORT.md`](./examples/pgvector-python-rag-index/docs/05-GRAPH-REPORT.md)
  - [`graph.html`](./examples/pgvector-python-rag-index/docs/graph.html) (interactive force-directed graph)

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## License

MIT License — see [LICENSE](./LICENSE).
