# pgvector-python — AST, Call/Type Hierarchy & Vectorless/PagedAttention RAG Index

| Metric | Value |
| :--- | :--- |
| **Source Files Scanned** | `74` |
| **AST Symbol Chunks (`chunks.jsonl`)** | `675` |
| **Types Mapped (`type_hierarchy.json`)** | `97` |
| **Super-Implementations Resolved** | `7` |
| **Production Symbols Linked to Tests** | `85` |
| **PagedAttention KV Pages (`512` tok/page)** | `124` (`86.4%` avg utilization) |

## Indexed Documentation
- **[`01-TREE-INDEX-VECTORLESS-RAG.md`](./01-TREE-INDEX-VECTORLESS-RAG.md)** — PageIndex hierarchical tree for Vectorless RAG
- **[`02-CALL-AND-TYPE-HIERARCHY.md`](./02-CALL-AND-TYPE-HIERARCHY.md)** — Callers, callees, supertypes, subtypes & super-implementations
- **[`03-REFERENCES-AND-TESTS-MAP.md`](./03-REFERENCES-AND-TESTS-MAP.md)** — Cross-file references & production-to-test traceability
- **[`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)** — KV-cache prefix blocks, PagedAttention virtual pages & `pgvector` schema
