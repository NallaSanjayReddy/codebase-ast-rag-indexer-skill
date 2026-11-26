#!/usr/bin/env python3
"""
Query Engine (v3.0) for codebase-ast-rag-indexer — Supports Vectorless, Vector, and Hybrid RRF RAG:
  --mode vectorless : Hierarchical Tree + 1-hop Knowledge Graph expansion (no embeddings required)
  --mode vector     : Real dual-vector cosine similarity search (nlp_vector + code_vector + priority boost)
  --mode hybrid     : Reciprocal Rank Fusion (RRF) combining Vector Cosine + SQLite FTS5 BM25 + Graph centrality
  --mode fts        : Local zero-server SQLite FTS5 BM25 + priority-path boosted search
  --mode explain    : Knowledge-graph node neighborhood (community, degree, confidence-tagged edges, rationale)
  --mode path       : BFS shortest path between --query and --target with weakest-hop confidence
  --mode symbol     : Full IDE/LSP card (definition, callers, callees, supertypes, subtypes, super_impl, refs, tests)
  --mode kv-pack    : Prefix-stable KV-Cache & PagedAttention-aligned context packet builder
"""
import argparse
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict, deque
from pathlib import Path

CONF_RANK = {"EXTRACTED": 3, "INFERRED": 2, "AMBIGUOUS": 1}


def load_chunks(index_dir: Path):
    chunks = []
    with (index_dir / "chunks.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def tokenize_query(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+", text)
    tokens = []
    for tok in raw:
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", tok).lower().split("_")
        for p in parts:
            if len(p) >= 2:
                tokens.append(p)
                if len(p) >= 4:
                    for i in range(len(p) - 2):
                        tokens.append("3g:" + p[i:i + 3])
    return tokens


def embed_query_tfidf(query: str, dim: int, idf: dict[str, float]) -> list[float]:
    toks = tokenize_query(query)
    vec = [0.0] * dim
    tf = Counter(toks)
    total = max(1, len(toks))
    for tok, cnt in tf.items():
        w = (cnt / total) * float(idf.get(tok, 1.5))
        h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=8).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[idx] += sign * w
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 1e-12 else vec


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def vector_search(index_dir: Path, query: str, top_k: int) -> list[dict]:
    meta_path = index_dir / "vector_meta.json"
    vec_path = index_dir / "vectors.jsonl"
    if not meta_path.exists() or not vec_path.exists():
        raise FileNotFoundError(f"Vector index not found in {index_dir}. Re-run indexer with --rag-mode both or vector.")
    vmeta = json.loads(meta_path.read_text(encoding="utf-8"))
    provider = vmeta.get("provider", "tfidf")
    dim = int(vmeta.get("dim", 128))

    if provider == "tfidf":
        q_vec = embed_query_tfidf(query, dim, vmeta.get("idf", {}))
    elif provider == "sentence-transformers":
        from sentence_transformers import SentenceTransformer  # type: ignore
        st = SentenceTransformer(vmeta.get("model", "all-MiniLM-L6-v2"))
        q_vec = [float(x) for x in st.encode([query], normalize_embeddings=True)[0]]
    else:
        q_vec = embed_query_tfidf(query, dim, vmeta.get("idf", {}))

    scored = []
    with vec_path.open(encoding="utf-8") as vf:
        for line in vf:
            if not line.strip():
                continue
            r = json.loads(line)
            sim_nlp = cosine(q_vec, r["nlp_vector"])
            sim_code = cosine(q_vec, r["code_vector"])
            blended = (0.6 * sim_nlp + 0.4 * sim_code) * float(r.get("priority_boost", 1.0))
            if blended > 0:
                scored.append({
                    "chunk_id": r["chunk_id"], "file": r["file"], "kind": r["kind"],
                    "community": r["community_label"], "kv_page_id": r["kv_page_id"],
                    "priority_boost": r["priority_boost"], "degree": r["degree"],
                    "nlp_cosine": round(sim_nlp, 4), "code_cosine": round(sim_code, 4),
                    "score": round(blended, 4),
                })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def query_sqlite_fts(index_dir: Path, query: str, top_k: int) -> list[dict]:
    db_path = index_dir / "rag_index.sqlite"
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite FTS5 index not found at {db_path}")
    tokens = [t for t in "".join(c if c.isalnum() or c == "_" else " " for c in query).split() if len(t) > 1]
    if not tokens:
        return []
    fts_expr = " OR ".join(f'"{t}"' for t in tokens)
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT m.chunk_id, m.kind, m.file, m.start_line, m.end_line, m.kv_page_id,
                   m.priority_boost, m.community_label, m.degree, m.signature,
                   (-bm25(chunks_fts)) * m.priority_boost AS boosted_score
            FROM chunks_fts
            JOIN chunk_meta m ON chunks_fts.chunk_id = m.chunk_id
            WHERE chunks_fts MATCH ?
            ORDER BY boosted_score DESC
            LIMIT ?
            """,
            (fts_expr, top_k),
        ).fetchall()
        return [
            {
                "chunk_id": r[0], "kind": r[1], "location": f"{r[2]}:{r[3]}-{r[4]}",
                "kv_page_id": r[5], "priority_boost": r[6], "community": r[7],
                "degree": r[8], "signature": r[9], "score": round(float(r[10]), 4),
            }
            for r in rows
        ]
    finally:
        conn.close()


def hybrid_rrf_search(index_dir: Path, query: str, top_k: int, rrf_k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion combining Vector Cosine + SQLite FTS5 BM25 + Knowledge Graph degree."""
    vec_hits = vector_search(index_dir, query, top_k * 3) if (index_dir / "vectors.jsonl").exists() else []
    fts_hits = query_sqlite_fts(index_dir, query, top_k * 3) if (index_dir / "rag_index.sqlite").exists() else []

    rrf_scores = defaultdict(float)
    sources = defaultdict(dict)

    for rank, h in enumerate(vec_hits, 1):
        cid = h["chunk_id"]
        rrf_scores[cid] += 1.0 / (rrf_k + rank)
        sources[cid]["vector_rank"] = rank
        sources[cid]["vector_score"] = h["score"]
        sources[cid]["meta"] = h

    for rank, h in enumerate(fts_hits, 1):
        cid = h["chunk_id"]
        rrf_scores[cid] += 1.0 / (rrf_k + rank)
        sources[cid]["fts_rank"] = rank
        sources[cid]["fts_score"] = h["score"]
        sources[cid].setdefault("meta", h)

    # Small graph centrality bonus (log-scaled degree) so core abstractions rise naturally
    results = []
    for cid, base_rrf in rrf_scores.items():
        meta = sources[cid]["meta"]
        deg = int(meta.get("degree", 0))
        graph_bonus = 0.002 * math.log1p(deg)
        results.append({
            "chunk_id": cid, "kind": meta.get("kind"), "community": meta.get("community"),
            "kv_page_id": meta.get("kv_page_id"), "degree": deg,
            "vector_rank": sources[cid].get("vector_rank"), "fts_rank": sources[cid].get("fts_rank"),
            "rrf_score": round(base_rrf + graph_bonus, 6),
        })
    results.sort(key=lambda x: x["rrf_score"], reverse=True)
    return results[:top_k]


def score_chunk(ch: dict, terms: list[str]) -> float:
    hay = f"{ch['chunk_id']} {ch['signature']} {ch['docstring']} {ch.get('nlp_text', '')} {ch['file']}".lower()
    score = 0.0
    for t in terms:
        if t in ch["name"].lower():
            score += 10.0
        elif t in ch["signature"].lower():
            score += 6.0
        elif t in hay:
            score += 3.0
    return score * float(ch.get("priority_boost", 1.0))


def resolve_node_id(query: str, nodes: list[dict]) -> dict | None:
    q = query.lower()
    for n in nodes:
        if n["id"].lower() == q or n["label"].lower() == q:
            return n
    for n in nodes:
        if q in n["id"].lower() or q in n["label"].lower():
            return n
    return None


def shortest_path(graph: dict, src_q: str, tgt_q: str):
    nodes = graph["nodes"]
    src_node = resolve_node_id(src_q, nodes)
    tgt_node = resolve_node_id(tgt_q, nodes)
    if not src_node or not tgt_node:
        return None, src_node, tgt_node

    adj = defaultdict(list)
    for e in graph["edges"]:
        adj[e["source"]].append((e["target"], e, "-->"))
        adj[e["target"]].append((e["source"], e, "<--"))

    q = deque([(src_node["id"], [])])
    visited = {src_node["id"]}
    while q:
        curr, path = q.popleft()
        if curr == tgt_node["id"]:
            return path, src_node, tgt_node
        for nxt, edge, arrow in adj.get(curr, []):
            if nxt not in visited:
                visited.add(nxt)
                q.append((nxt, path + [(curr, arrow, edge, nxt)]))
    return [], src_node, tgt_node


def main():
    parser = argparse.ArgumentParser(description="Query Dual Vector + Vectorless AST/Knowledge-Graph RAG Index")
    parser.add_argument("--index", required=True, help="Path to generated index/ directory")
    parser.add_argument("--query", required=True, help="Symbol name, start node (for path), or natural-language query")
    parser.add_argument("--target", default="", help="Target symbol name (required for --mode path)")
    parser.add_argument(
        "--mode",
        choices=["vectorless", "vector", "hybrid", "fts", "explain", "path", "symbol", "kv-pack"],
        default="hybrid",
    )
    parser.add_argument("--top-k", type=int, default=6)
    args = parser.parse_args()

    idx_dir = Path(args.index).resolve()

    if args.mode == "vector":
        hits = vector_search(idx_dir, args.query, args.top_k)
        print(json.dumps({"mode": "vector", "query": args.query, "results": hits}, indent=2))
        return

    if args.mode == "hybrid":
        hits = hybrid_rrf_search(idx_dir, args.query, args.top_k)
        print(json.dumps({"mode": "hybrid_rrf", "query": args.query, "results": hits}, indent=2))
        return

    if args.mode == "fts":
        hits = query_sqlite_fts(idx_dir, args.query, args.top_k)
        print(json.dumps({"mode": "fts", "query": args.query, "results": hits}, indent=2))
        return

    if args.mode == "explain":
        graph = json.loads((idx_dir / "graph.json").read_text(encoding="utf-8"))
        chunks = {c["chunk_id"]: c for c in load_chunks(idx_dir)}
        node = resolve_node_id(args.query, graph["nodes"])
        if not node:
            print(f"No symbol matching '{args.query}' found in graph.json")
            return
        ch = chunks.get(node["id"], {})
        inc = [e for e in graph["edges"] if e["target"] == node["id"]]
        out = [e for e in graph["edges"] if e["source"] == node["id"]]
        print(f"Node: {node['id']}")
        print(f"  Source:    {node['file']}:{node['line']} (KV-Page {node['kv_page_id']})")
        print(f"  Community: #{node['community']} ({node['community_label']})")
        print(f"  Degree:    {node['degree']}")
        if ch.get("signature"):
            print(f"  Signature: {ch['signature']}")
        if ch.get("super_implementation"):
            print(f"  Overrides: {ch['super_implementation']}")
        if ch.get("rationale"):
            for r in ch["rationale"][:3]:
                print(f"  [{r['tag']}]:   {r['text']} (L{r['line']})")
        print(f"\nOutgoing Connections ({len(out)}):")
        for e in out[:12]:
            print(f"  --> {e['target']} [{e['relation']}] [{e['confidence']}]")
        print(f"\nIncoming Connections ({len(inc)}):")
        for e in inc[:12]:
            print(f"  <-- {e['source']} [{e['relation']}] [{e['confidence']}]")
        return

    if args.mode == "path":
        if not args.target:
            raise SystemExit("--target is required for --mode path")
        graph = json.loads((idx_dir / "graph.json").read_text(encoding="utf-8"))
        path, src_n, tgt_n = shortest_path(graph, args.query, args.target)
        if not src_n or not tgt_n:
            print(f"Could not resolve endpoints: source={src_n is not None}, target={tgt_n is not None}")
            return
        if not path:
            print(f"No path found between {src_n['id']} and {tgt_n['id']}.")
            return
        weakest = min((e["confidence"] for _, _, e, _ in path), key=lambda c: CONF_RANK.get(c, 0))
        print(f"Shortest path ({len(path)} hops) | Overall confidence (weakest hop): [{weakest}]")
        parts = [src_n["id"]]
        for _, arrow, edge, nxt in path:
            parts.append(f" {arrow}[{edge['relation']}|{edge['confidence']}]{arrow} {nxt}")
        print(" ".join(parts))
        return

    chunks = load_chunks(idx_dir)
    terms = [t.lower() for t in args.query.replace(".", " ").split() if len(t) > 1]
    ranked = sorted(chunks, key=lambda c: score_chunk(c, terms), reverse=True)
    hits = [c for c in ranked if score_chunk(c, terms) > 0][:args.top_k]

    if args.mode == "symbol":
        refs = json.loads((idx_dir / "references.json").read_text(encoding="utf-8"))
        out = [{
            "symbol": h["chunk_id"],
            "definition": f"{h['file']}:{h['start_line']}-{h['end_line']}",
            "signature": h["signature"],
            "community": h.get("community_label"),
            "degree": h.get("degree", 0),
            "callers": h["callers"],
            "callees": h["callees"],
            "super_types": h["super_types"],
            "sub_types": h["sub_types"],
            "super_implementation": h["super_implementation"],
            "type_definitions": h["type_definitions"],
            "rationale": h.get("rationale", []),
            "references": refs.get(h["chunk_id"], [])[:10],
            "tests": h["tests"],
        } for h in hits]
        print(json.dumps(out, indent=2))

    elif args.mode == "vectorless":
        # Vectorless Tree + 1-hop Knowledge Graph Subgraph expansion (graphify pattern)
        graph_edges = json.loads((idx_dir / "graph.json").read_text(encoding="utf-8"))["edges"] if (idx_dir / "graph.json").exists() else []
        print(f"# Vectorless Tree + 1-Hop Graph Subgraph for: '{args.query}'\n")
        for h in hits:
            cid = h["chunk_id"]
            print(f"- **{cid}** (`{h['kind']}` @ `{h['file']}:{h['start_line']}-{h['end_line']}` | KV-Page `{h['kv_page_id']}` | Comm `{h.get('community_label')}` | deg=`{h.get('degree', 0)}`)")
            print(f"  - Signature: `{h['signature']}`")
            hop_edges = [e for e in graph_edges if e["source"] == cid or e["target"] == cid][:5]
            for e in hop_edges:
                arrow = f"--> {e['target']}" if e["source"] == cid else f"<-- {e['source']}"
                print(f"  - Graph 1-hop: `{arrow}` [`{e['relation']}` | `{e['confidence']}`]")
            if h.get("tests"):
                print(f"  - Tests ({len(h['tests'])}): {', '.join(t['test_id'] for t in h['tests'][:3])}")

    elif args.mode == "kv-pack":
        hits_canonical = sorted(hits, key=lambda c: (c["kv_page_id"], c["kv_token_offset"]))
        pages_used = sorted({h["kv_page_id"] for h in hits_canonical})
        print("<<<STATIC_KV_PREFIX_START>>>")
        print(f"# PagedAttention Block Table: pages={pages_used} | total_chunks={len(hits_canonical)}")
        for h in hits_canonical:
            print(f"\n## [KV-Page {h['kv_page_id']} | offset={h['kv_token_offset']} | sha256={h['sha256']} | comm={h.get('community_label')}] {h['chunk_id']}")
            print(f"# File: {h['file']}:{h['start_line']}-{h['end_line']} | SuperImpl: {h['super_implementation']} | Tests: {[t['test_id'] for t in h['tests'][:3]]}")
            print(h["code"])
        print("\n<<<STATIC_KV_PREFIX_END>>>")
        print(f"<<<DYNAMIC_QUERY_SUFFIX>>>\nUser Query: {args.query}")


if __name__ == "__main__":
    main()
