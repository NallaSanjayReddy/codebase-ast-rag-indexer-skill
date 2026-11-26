#!/usr/bin/env python3
"""
Query Engine for codebase-ast-rag-indexer:
  --mode vectorless : Hierarchical Tree-Based (PageIndex) retrieval without embeddings
  --mode symbol     : Full IDE/LSP card (definition, callers, callees, supertypes, subtypes, super_impl, refs, tests)
  --mode kv-pack    : Prefix-stable KV-Cache & PagedAttention-aligned context packet builder
"""
import argparse
import json
from pathlib import Path


def load_chunks(index_dir: Path):
    chunks = []
    with (index_dir / "chunks.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def score_chunk(ch: dict, terms: list[str]) -> int:
    hay = f"{ch['chunk_id']} {ch['signature']} {ch['docstring']} {ch['file']}".lower()
    score = 0
    for t in terms:
        if t in ch["name"].lower():
            score += 10
        elif t in ch["signature"].lower():
            score += 6
        elif t in hay:
            score += 3
    return score


def main():
    parser = argparse.ArgumentParser(description="Query AST/Vectorless RAG Index & Pack KV-Cache PagedAttention Context")
    parser.add_argument("--index", required=True, help="Path to generated index/ directory")
    parser.add_argument("--query", required=True, help="Symbol name or natural-language search query")
    parser.add_argument("--mode", choices=["vectorless", "symbol", "kv-pack"], default="kv-pack")
    parser.add_argument("--top-k", type=int, default=6)
    args = parser.parse_args()

    idx_dir = Path(args.index).resolve()
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
            "callers": h["callers"],
            "callees": h["callees"],
            "super_types": h["super_types"],
            "sub_types": h["sub_types"],
            "super_implementation": h["super_implementation"],
            "type_definitions": h["type_definitions"],
            "references": refs.get(h["chunk_id"], [])[:10],
            "tests": h["tests"],
        } for h in hits]
        print(json.dumps(out, indent=2))

    elif args.mode == "vectorless":
        print(f"# Vectorless RAG Tree Matches for: '{args.query}'\n")
        for h in hits:
            print(f"- **{h['chunk_id']}** (`{h['kind']}` @ `{h['file']}:{h['start_line']}-{h['end_line']}` | KV-Page `{h['kv_page_id']}`)")
            print(f"  - Signature: `{h['signature']}`")
            print(f"  - Callers ({len(h['callers'])}): {', '.join(h['callers'][:4]) or 'none'}")
            print(f"  - Callees ({len(h['callees'])}): {', '.join(h['callees'][:4]) or 'none'}")
            print(f"  - Tests ({len(h['tests'])}): {', '.join(t['test_id'] for t in h['tests'][:3]) or 'none'}")

    elif args.mode == "kv-pack":
        hits_canonical = sorted(hits, key=lambda c: (c["kv_page_id"], c["kv_token_offset"]))
        pages_used = sorted({h["kv_page_id"] for h in hits_canonical})
        print("<<<STATIC_KV_PREFIX_START>>>")
        print(f"# PagedAttention Block Table: pages={pages_used} | total_chunks={len(hits_canonical)}")
        for h in hits_canonical:
            print(f"\n## [KV-Page {h['kv_page_id']} | offset={h['kv_token_offset']} | sha256={h['sha256']}] {h['chunk_id']}")
            print(f"# File: {h['file']}:{h['start_line']}-{h['end_line']} | SuperImpl: {h['super_implementation']} | Tests: {[t['test_id'] for t in h['tests'][:3]]}")
            print(h["code"])
        print("\n<<<STATIC_KV_PREFIX_END>>>")
        print(f"<<<DYNAMIC_QUERY_SUFFIX>>>\nUser Query: {args.query}")


if __name__ == "__main__":
    main()
