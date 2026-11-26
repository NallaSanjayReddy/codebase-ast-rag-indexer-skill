# pgvector-python — Dual Vector & Vectorless AST RAG Index (`v3.0.0`)

| Metric | Value |
| :--- | :--- |
| **RAG Mode / Chunk Strategy** | `both` / `hybrid` |
| **Vector Embeddings (`vectors.jsonl` + SQLite + Qdrant)** | `tfidf` (`dim=128`, `675` dual vectors) |
| **Source Files Scanned** | `74` |
| **AST Symbol Chunks (`chunks.jsonl` + `rag_index.sqlite`)** | `675` |
| **Knowledge Graph Edges (`graph.json`)** | `2491` (`EXTRACTED=1275`, `INFERRED=479`, `AMBIGUOUS=737`) |
| **Production Subsystem Communities / Import Cycles** | `15` communities / `0` cycles |
| **Types Mapped / Super-Implementations** | `97` types / `7` overrides |
| **Production Symbols Linked to Tests** | `71` |
| **PagedAttention KV Pages (`512` tok/page)** | `124` (`86.4%` avg utilization) |

## Indexed Documentation & Interactive Graph
- **[`01-TREE-INDEX-VECTORLESS-RAG.md`](./01-TREE-INDEX-VECTORLESS-RAG.md)** — PageIndex hierarchical tree for Vectorless RAG
- **[`02-CALL-AND-TYPE-HIERARCHY.md`](./02-CALL-AND-TYPE-HIERARCHY.md)** — Callers, callees, supertypes, subtypes & super-implementations
- **[`03-REFERENCES-AND-TESTS-MAP.md`](./03-REFERENCES-AND-TESTS-MAP.md)** — Cross-file references & production-to-test traceability
- **[`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)** — KV-cache prefix blocks, PagedAttention virtual pages & dual-embedding `pgvector`/Qdrant stores
- **[`05-GRAPH-REPORT.md`](./05-GRAPH-REPORT.md)** — God Nodes, Subsystem Communities, Surprising Cross-Community Bridges, Import Cycles & Rationale Notes
- **[`graph.html`](./graph.html)** — Self-contained interactive force-directed knowledge graph viewer
