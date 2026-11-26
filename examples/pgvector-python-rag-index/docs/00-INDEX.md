# pgvector-python — AST, Knowledge Graph, Vectorless & PagedAttention RAG Index

| Metric | Value |
| :--- | :--- |
| **Schema Version / Chunk Strategy** | `v2.0.0` / `hybrid` |
| **Source Files Scanned** | `74` |
| **AST Symbol Chunks (`chunks.jsonl` + `rag_index.sqlite`)** | `675` |
| **Knowledge Graph Edges (`graph.json`)** | `3619` (`EXTRACTED=1447`, `INFERRED=485`, `AMBIGUOUS=1687`) |
| **Detected Subsystem Communities** | `3` |
| **Types Mapped (`type_hierarchy.json`)** | `97` |
| **Super-Implementations Resolved** | `7` |
| **Production Symbols Linked to Tests** | `85` |
| **PagedAttention KV Pages (`512` tok/page)** | `124` (`86.4%` avg utilization) |

## Indexed Documentation & Interactive Graph
- **[`01-TREE-INDEX-VECTORLESS-RAG.md`](./01-TREE-INDEX-VECTORLESS-RAG.md)** — PageIndex hierarchical tree for Vectorless RAG
- **[`02-CALL-AND-TYPE-HIERARCHY.md`](./02-CALL-AND-TYPE-HIERARCHY.md)** — Callers, callees, supertypes, subtypes & super-implementations
- **[`03-REFERENCES-AND-TESTS-MAP.md`](./03-REFERENCES-AND-TESTS-MAP.md)** — Cross-file references & production-to-test traceability
- **[`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)** — KV-cache prefix blocks, PagedAttention virtual pages & dual-embedding `pgvector` schema
- **[`05-GRAPH-REPORT.md`](./05-GRAPH-REPORT.md)** — God Nodes, Subsystem Communities, Surprising Cross-Community Bridges & Rationale Notes
- **[`graph.html`](./graph.html)** — Self-contained interactive force-directed knowledge graph viewer
