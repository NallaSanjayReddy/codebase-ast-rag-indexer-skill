#!/usr/bin/env python3
"""
Codebase AST, Call/Type Hierarchy, Vectorless RAG & KV-Cache/PagedAttention Indexer.
Clones any GitHub URL (or scans a local repo) and builds:
  - AST-aware hierarchical chunks (chunks.jsonl)
  - Vectorless RAG Tree Index (tree_index.json)
  - Bidirectional Call Hierarchy (call_graph.json)
  - Type Hierarchy: supertypes, subtypes, implementations, super-implementations, type definitions (type_hierarchy.json)
  - Cross-file References (references.json) & Test Traceability (test_map.json)
  - KV-Cache Prefix-Stable & PagedAttention Virtual Token Page Allocation (kv_paged_blocks.json)
  - PostgreSQL pgvector Hybrid RRF Schema (pgvector_schema.sql)
  - 5 Cross-Linked Markdown Docs (docs/00-INDEX.md -> 04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)
"""
import argparse
import ast
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "target", "build", "dist", "out", ".gradle",
    ".idea", ".vscode", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache"
}
CODE_EXTS = {".py", ".java", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".kt", ".cs"}


def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4.0))


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def parse_python_file(rel_path: str, source: str, is_test: bool):
    symbols, calls, imports = [], [], []
    lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError:
        return symbols, calls, imports

    mod_id = rel_path.replace("/", ".").removesuffix(".py")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for alias in node.names:
                imports.append((f"{base}.{alias.name}".strip("."), node.lineno))

    def get_ann(ann):
        if ann is None:
            return None
        try:
            return ast.unparse(ann)
        except Exception:
            return None

    def extract_calls_in_body(func_node, caller_id):
        for sub in ast.walk(func_node):
            if isinstance(sub, ast.Call):
                cname = sub.func.id if isinstance(sub.func, ast.Name) else (
                    sub.func.attr if isinstance(sub.func, ast.Attribute) else None
                )
                if cname:
                    calls.append((caller_id, cname, getattr(sub, "lineno", func_node.lineno)))

    def visit_block(body, parent_id=None, parent_class=None):
        for node in body:
            if isinstance(node, ast.ClassDef):
                cid = f"{mod_id}.{node.name}" if not parent_class else f"{parent_id}.{node.name}"
                bases = [get_ann(b) for b in node.bases if get_ann(b)]
                s_ln, e_ln = node.lineno, getattr(node, "end_lineno", node.lineno)
                code_slice = "\n".join(lines[s_ln - 1:e_ln])
                doc = ast.get_docstring(node) or ""
                symbols.append({
                    "id": cid, "name": node.name, "kind": "class", "language": "Python",
                    "file": rel_path, "start_line": s_ln, "end_line": e_ln,
                    "parent_id": parent_id or mod_id,
                    "signature": f"class {node.name}({', '.join(bases)}):" if bases else f"class {node.name}:",
                    "docstring": doc.splitlines()[0] if doc else "",
                    "super_types": bases, "param_types": [], "return_type": None,
                    "is_test": is_test or node.name.startswith("Test"),
                    "code": code_slice, "tokens": est_tokens(code_slice), "sha256": sha256_short(code_slice),
                })
                visit_block(node.body, parent_id=cid, parent_class=node.name)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fid = f"{parent_id}.{node.name}" if parent_id else f"{mod_id}.{node.name}"
                s_ln, e_ln = node.lineno, getattr(node, "end_lineno", node.lineno)
                code_slice = "\n".join(lines[s_ln - 1:e_ln])
                args_str, p_types = [], []
                for a in node.args.args:
                    t_ann = get_ann(a.annotation)
                    if t_ann:
                        p_types.append(t_ann)
                        args_str.append(f"{a.arg}: {t_ann}")
                    else:
                        args_str.append(a.arg)
                ret_t = get_ann(node.returns)
                prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                sig = f"{prefix} {node.name}({', '.join(args_str)})" + (f" -> {ret_t}" if ret_t else "")
                doc = ast.get_docstring(node) or ""
                symbols.append({
                    "id": fid, "name": node.name, "kind": "method" if parent_class else "function",
                    "language": "Python", "file": rel_path, "start_line": s_ln, "end_line": e_ln,
                    "parent_id": parent_id or mod_id, "parent_class": parent_class,
                    "signature": sig, "docstring": doc.splitlines()[0] if doc else "",
                    "super_types": [], "param_types": p_types, "return_type": ret_t,
                    "is_test": is_test or node.name.startswith("test_"),
                    "code": code_slice, "tokens": est_tokens(code_slice), "sha256": sha256_short(code_slice),
                })
                extract_calls_in_body(node, fid)

    visit_block(tree.body)
    return symbols, calls, imports


def parse_generic_file(rel_path: str, source: str, ext: str, is_test: bool):
    symbols, calls, imports = [], [], []
    lines = source.splitlines()
    lang_map = {".java": "Java", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
                ".jsx": "JavaScript", ".go": "Go", ".rs": "Rust", ".kt": "Kotlin", ".cs": "C#"}
    lang = lang_map.get(ext, "Code")
    mod_id = rel_path.replace("/", ".").removesuffix(ext)

    for idx, ln in enumerate(lines, 1):
        m = re.match(r"^\s*(?:import|use|using)\s+([^;]+)", ln)
        if m:
            imports.append((m.group(1).strip(), idx))

    cls_pat = re.compile(
        r"\b(class|interface|enum|record|struct|trait)\s+([A-Za-z_][A-Za-z0-9_]*)(?:<[^>]+>)?"
        r"(?:\s+extends\s+([A-Za-z0-9_.,\s<>]+?))?(?:\s+implements\s+([A-Za-z0-9_.,\s<>]+?))?\s*\{"
    )
    fn_pat = re.compile(
        r"(?:public|private|protected|static|async|export|func|fn|def|\s)+\s*"
        r"(?:([A-Za-z0-9_<>\[\]\.?]+)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]{0,160})\)"
        r"\s*(?::\s*([A-Za-z0-9_<>\[\]|]+))?\s*\{"
    )

    def find_block_end(start_idx):
        depth, opened = 0, False
        for j in range(start_idx, min(len(lines), start_idx + 250)):
            for ch in lines[j]:
                if ch == "{":
                    depth += 1
                    opened = True
                elif ch == "}":
                    depth -= 1
                    if opened and depth == 0:
                        return j + 1
        return min(len(lines), start_idx + 25)

    current_class = None
    for i, ln in enumerate(lines):
        cm = cls_pat.search(ln)
        if cm:
            kind, cname, ext_s, imp_s = cm.group(1), cm.group(2), cm.group(3), cm.group(4)
            supers = []
            for raw_s in (ext_s, imp_s):
                if raw_s:
                    for part in raw_s.split(","):
                        cleaned = re.sub(r"<.*>", "", part).strip()
                        if cleaned:
                            supers.append(cleaned)
            e_ln = find_block_end(i)
            code_slice = "\n".join(lines[i:e_ln])
            cid = f"{mod_id}.{cname}"
            current_class = cid
            symbols.append({
                "id": cid, "name": cname, "kind": kind, "language": lang,
                "file": rel_path, "start_line": i + 1, "end_line": e_ln,
                "parent_id": mod_id, "signature": ln.strip().rstrip("{").strip(),
                "docstring": "", "super_types": supers, "param_types": [], "return_type": None,
                "is_test": is_test or "Test" in cname, "code": code_slice,
                "tokens": est_tokens(code_slice), "sha256": sha256_short(code_slice),
            })
            continue

        fm = fn_pat.search(ln)
        if fm:
            ret_t, fname, params_s, ts_ret = fm.group(1), fm.group(2), fm.group(3), fm.group(4)
            if fname in ("if", "for", "while", "switch", "catch", "synchronized", "return"):
                continue
            e_ln = find_block_end(i)
            code_slice = "\n".join(lines[i:e_ln])
            fid = f"{current_class}.{fname}" if current_class else f"{mod_id}.{fname}"
            symbols.append({
                "id": fid, "name": fname, "kind": "method" if current_class else "function", "language": lang,
                "file": rel_path, "start_line": i + 1, "end_line": e_ln,
                "parent_id": current_class or mod_id,
                "parent_class": current_class.split(".")[-1] if current_class else None,
                "signature": ln.strip().rstrip("{").strip(), "docstring": "",
                "super_types": [], "param_types": [p.strip() for p in params_s.split(",") if p.strip()],
                "return_type": ts_ret or ret_t, "is_test": is_test or fname.lower().startswith("test"),
                "code": code_slice, "tokens": est_tokens(code_slice), "sha256": sha256_short(code_slice),
            })
            for call_m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", code_slice):
                if call_m.group(1) != fname and call_m.group(1) not in ("if", "for", "while", "switch", "catch", "new"):
                    calls.append((fid, call_m.group(1), i + 1))

    return symbols, calls, imports


def build_full_rag_index(repo_path: Path, repo_name: str, page_size: int = 512):
    all_symbols, raw_calls = [], []
    files_scanned = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in sorted(files):
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()
            if ext not in CODE_EXTS:
                continue
            rel_path = str(fpath.relative_to(repo_path)).replace("\\", "/")
            is_test = ("test" in rel_path.lower() or "spec" in fname.lower())
            try:
                source = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_scanned += 1
            syms, cls, _ = parse_python_file(rel_path, source, is_test) if ext == ".py" else parse_generic_file(rel_path, source, ext, is_test)
            all_symbols.extend(syms)
            raw_calls.extend(cls)

    by_id = {s["id"]: s for s in all_symbols}
    by_name = defaultdict(list)
    class_methods = defaultdict(dict)
    for s in all_symbols:
        by_name[s["name"]].append(s["id"])
        if s["kind"] == "method" and s.get("parent_class"):
            class_methods[s["parent_class"]][s["name"]] = s["id"]

    outgoing_calls, incoming_calls = defaultdict(set), defaultdict(set)
    references = defaultdict(list)
    for caller_id, callee_name, line in raw_calls:
        targets = by_name.get(callee_name, [])
        caller_file = by_id[caller_id]["file"] if caller_id in by_id else ""
        for tid in targets[:4]:
            if tid != caller_id:
                outgoing_calls[caller_id].add(tid)
                incoming_calls[tid].add(caller_id)
                references[tid].append({"from_symbol": caller_id, "file": caller_file, "line": line, "kind": "call"})

    type_hierarchy, sub_types = {}, defaultdict(list)
    super_impls, type_defs = {}, defaultdict(list)
    for s in all_symbols:
        if s["kind"] in ("class", "interface", "enum", "record", "struct", "trait"):
            resolved_supers = []
            for st in s["super_types"]:
                matched = by_name.get(st.split(".")[-1], [])
                if matched:
                    for mid in matched[:2]:
                        resolved_supers.append(mid)
                        sub_types[mid].append(s["id"])
                        references[mid].append({"from_symbol": s["id"], "file": s["file"], "line": s["start_line"], "kind": "extends/implements"})
                else:
                    resolved_supers.append(st)
            type_hierarchy[s["id"]] = {
                "kind": s["kind"], "file": s["file"], "line": s["start_line"],
                "super_types": resolved_supers, "sub_types": [], "implementations": [],
            }

    for tid, info in type_hierarchy.items():
        children = sub_types.get(tid, [])
        info["sub_types"] = children
        info["implementations"] = [c for c in children if by_id.get(c, {}).get("kind") == "class"]

    for s in all_symbols:
        if s["kind"] == "method" and s.get("parent_class") and s["parent_id"] in type_hierarchy:
            for sup_id in type_hierarchy[s["parent_id"]]["super_types"]:
                sup_name = sup_id.split(".")[-1]
                if s["name"] in class_methods.get(sup_name, {}):
                    super_impls[s["id"]] = class_methods[sup_name][s["name"]]
        for ann in list(s.get("param_types", [])) + ([s["return_type"]] if s.get("return_type") else []):
            for tok in re.findall(r"\b([A-Z][A-Za-z0-9_]+)\b", str(ann)):
                for td_id in by_name.get(tok, [])[:2]:
                    if td_id not in type_defs[s["id"]]:
                        type_defs[s["id"]].append(td_id)

    test_map = defaultdict(list)
    for ts in [s for s in all_symbols if s["is_test"]]:
        for callee_id in outgoing_calls.get(ts["id"], []):
            if not by_id[callee_id]["is_test"]:
                test_map[callee_id].append({"test_id": ts["id"], "file": ts["file"], "line": ts["start_line"], "link": "direct_call"})
        low_t = ts["name"].lower()
        for prod_name, prod_ids in by_name.items():
            if len(prod_name) >= 4 and prod_name.lower() in low_t:
                for pid in prod_ids[:2]:
                    if not by_id[pid]["is_test"]:
                        entry = {"test_id": ts["id"], "file": ts["file"], "line": ts["start_line"], "link": "name_match"}
                        if entry not in test_map[pid]:
                            test_map[pid].append(entry)

    canonical_symbols = sorted(all_symbols, key=lambda s: (s["is_test"], s["file"], s["start_line"], s["id"]))
    kv_pages, chunks = [], []
    cur_page = {"kv_page_id": 0, "capacity_tokens": page_size, "used_tokens": 0, "chunks": []}

    for s in canonical_symbols:
        toks = min(s["tokens"], page_size)
        if cur_page["used_tokens"] + toks > page_size and cur_page["chunks"]:
            cur_page["prefix_hash"] = sha256_short("|".join(cur_page["chunks"]))
            cur_page["utilization_pct"] = round(cur_page["used_tokens"] * 100.0 / page_size, 1)
            kv_pages.append(cur_page)
            cur_page = {"kv_page_id": len(kv_pages), "capacity_tokens": page_size, "used_tokens": 0, "chunks": []}

        page_id, token_offset = cur_page["kv_page_id"], cur_page["used_tokens"]
        cur_page["chunks"].append(s["id"])
        cur_page["used_tokens"] += toks
        chunks.append({
            "chunk_id": s["id"], "name": s["name"], "kind": s["kind"], "language": s["language"],
            "file": s["file"], "start_line": s["start_line"], "end_line": s["end_line"],
            "parent_id": s["parent_id"], "signature": s["signature"], "docstring": s["docstring"],
            "token_count": s["tokens"], "sha256": s["sha256"],
            "kv_page_id": page_id, "kv_token_offset": token_offset,
            "callers": sorted(incoming_calls.get(s["id"], [])),
            "callees": sorted(outgoing_calls.get(s["id"], [])),
            "super_types": type_hierarchy.get(s["id"], {}).get("super_types", []),
            "sub_types": type_hierarchy.get(s["id"], {}).get("sub_types", []),
            "super_implementation": super_impls.get(s["id"]),
            "type_definitions": type_defs.get(s["id"], []),
            "references_count": len(references.get(s["id"], [])),
            "tests": test_map.get(s["id"], [])[:8],
            "is_test": s["is_test"], "code": s["code"][:3000],
        })

    if cur_page["chunks"]:
        cur_page["prefix_hash"] = sha256_short("|".join(cur_page["chunks"]))
        cur_page["utilization_pct"] = round(cur_page["used_tokens"] * 100.0 / page_size, 1)
        kv_pages.append(cur_page)

    tree_index = {"repo": repo_name, "total_files": files_scanned, "total_symbols": len(all_symbols), "modules": {}}
    for c in chunks:
        mod = c["file"].split("/")[0] if "/" in c["file"] else "root"
        mod_node = tree_index["modules"].setdefault(mod, {"files": {}, "symbol_count": 0, "total_tokens": 0})
        mod_node["symbol_count"] += 1
        mod_node["total_tokens"] += c["token_count"]
        f_node = mod_node["files"].setdefault(c["file"], {"symbols": []})
        f_node["symbols"].append({
            "id": c["chunk_id"], "kind": c["kind"], "signature": c["signature"],
            "lines": f"{c['start_line']}-{c['end_line']}", "kv_page_id": c["kv_page_id"],
            "callers": len(c["callers"]), "callees": len(c["callees"]), "tests": len(c["tests"]),
        })

    return {
        "repo_name": repo_name, "files_scanned": files_scanned, "chunks": chunks,
        "tree_index": tree_index,
        "call_graph": {"outgoing": {k: sorted(v) for k, v in outgoing_calls.items()},
                       "incoming": {k: sorted(v) for k, v in incoming_calls.items()}},
        "type_hierarchy": type_hierarchy, "super_implementations": super_impls,
        "type_definitions": dict(type_defs), "references": dict(references),
        "test_map": dict(test_map), "kv_pages": kv_pages, "page_size": page_size,
    }


def write_outputs(bundle: dict, out_dir: Path):
    idx_dir, docs_dir = out_dir / "index", out_dir / "docs"
    idx_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    with (idx_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for ch in bundle["chunks"]:
            f.write(json.dumps(ch) + "\n")

    (idx_dir / "tree_index.json").write_text(json.dumps(bundle["tree_index"], indent=2), encoding="utf-8")
    (idx_dir / "call_graph.json").write_text(json.dumps(bundle["call_graph"], indent=2), encoding="utf-8")
    (idx_dir / "type_hierarchy.json").write_text(json.dumps({
        "types": bundle["type_hierarchy"],
        "super_implementations": bundle["super_implementations"],
        "type_definitions": bundle["type_definitions"],
    }, indent=2), encoding="utf-8")
    (idx_dir / "references.json").write_text(json.dumps(bundle["references"], indent=2), encoding="utf-8")
    (idx_dir / "test_map.json").write_text(json.dumps(bundle["test_map"], indent=2), encoding="utf-8")
    (idx_dir / "kv_paged_blocks.json").write_text(json.dumps({
        "page_size_tokens": bundle["page_size"], "total_pages": len(bundle["kv_pages"]), "pages": bundle["kv_pages"],
    }, indent=2), encoding="utf-8")

    (idx_dir / "pgvector_schema.sql").write_text("""-- PostgreSQL pgvector 0.8+ Hybrid AST RAG Schema (HNSW halfvec + GIN tsvector)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS code_ast_chunks (
    chunk_id TEXT PRIMARY KEY, repo_name TEXT NOT NULL, file_path TEXT NOT NULL,
    kind TEXT NOT NULL, signature TEXT NOT NULL, parent_id TEXT,
    start_line INT NOT NULL, end_line INT NOT NULL, kv_page_id INT NOT NULL,
    token_count INT NOT NULL, sha256 TEXT NOT NULL,
    callers JSONB NOT NULL DEFAULT '[]'::jsonb, callees JSONB NOT NULL DEFAULT '[]'::jsonb,
    super_types JSONB NOT NULL DEFAULT '[]'::jsonb, super_implementation TEXT,
    tests JSONB NOT NULL DEFAULT '[]'::jsonb, code TEXT NOT NULL,
    fts TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', signature || ' ' || code)) STORED,
    embedding HALFVEC(1536)
);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_hnsw ON code_ast_chunks USING hnsw (embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_fts  ON code_ast_chunks USING gin (fts);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_page ON code_ast_chunks (repo_name, kv_page_id);
""", encoding="utf-8")

    rname = bundle["repo_name"]
    n_pages = len(bundle["kv_pages"])
    avg_util = round(sum(p["utilization_pct"] for p in bundle["kv_pages"]) / max(1, n_pages), 1)
    (docs_dir / "00-INDEX.md").write_text(f"""# {rname} — AST, Call/Type Hierarchy & Vectorless/PagedAttention RAG Index

| Metric | Value |
| :--- | :--- |
| **Source Files Scanned** | `{bundle["files_scanned"]}` |
| **AST Symbol Chunks (`chunks.jsonl`)** | `{len(bundle["chunks"])}` |
| **Types Mapped (`type_hierarchy.json`)** | `{len(bundle["type_hierarchy"])}` |
| **Super-Implementations Resolved** | `{len(bundle["super_implementations"])}` |
| **Production Symbols Linked to Tests** | `{len(bundle["test_map"])}` |
| **PagedAttention KV Pages (`{bundle["page_size"]}` tok/page)** | `{n_pages}` (`{avg_util}%` avg utilization) |

## Indexed Documentation
- **[`01-TREE-INDEX-VECTORLESS-RAG.md`](./01-TREE-INDEX-VECTORLESS-RAG.md)** — PageIndex hierarchical tree for Vectorless RAG
- **[`02-CALL-AND-TYPE-HIERARCHY.md`](./02-CALL-AND-TYPE-HIERARCHY.md)** — Callers, callees, supertypes, subtypes & super-implementations
- **[`03-REFERENCES-AND-TESTS-MAP.md`](./03-REFERENCES-AND-TESTS-MAP.md)** — Cross-file references & production-to-test traceability
- **[`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)** — KV-cache prefix blocks, PagedAttention virtual pages & `pgvector` schema
""", encoding="utf-8")

    tree_lines = [f"# 01 — Vectorless RAG Tree Index (`{rname}`)\n", "[← 00-INDEX.md](./00-INDEX.md)\n"]
    for mod, mdata in sorted(bundle["tree_index"]["modules"].items()):
        tree_lines.append(f"## Module `{mod}` ({mdata['symbol_count']} symbols, ~{mdata['total_tokens']:,} tokens)")
        for fpath, fdata in sorted(mdata["files"].items())[:25]:
            tree_lines.append(f"- **`{fpath}`**")
            for sym in fdata["symbols"][:12]:
                tree_lines.append(f"  - `{sym['kind']}` **`{sym['id']}`** (L{sym['lines']}, KV-Page `{sym['kv_page_id']}`, callers=`{sym['callers']}`, callees=`{sym['callees']}`, tests=`{sym['tests']}`)")
    (docs_dir / "01-TREE-INDEX-VECTORLESS-RAG.md").write_text("\n".join(tree_lines), encoding="utf-8")

    ct_lines = [f"# 02 — Call Hierarchy, Type Hierarchy & Super-Implementations (`{rname}`)\n", "[← 00-INDEX.md](./00-INDEX.md)\n",
                "| Type | Kind | Super Types | Sub Types / Implementations | Location |", "| :--- | :--- | :--- | :--- | :--- |"]
    for tid, tinfo in list(bundle["type_hierarchy"].items())[:40]:
        ct_lines.append(f"| `{tid}` | {tinfo['kind']} | {', '.join(f'`{x}`' for x in tinfo['super_types']) or '—'} | {', '.join(f'`{x}`' for x in tinfo['sub_types']) or '—'} | `{tinfo['file']}:{tinfo['line']}` |")
    ct_lines.append("\n## Super-Implementations (Method Overrides)\n")
    for child_m, parent_m in list(bundle["super_implementations"].items())[:30]:
        ct_lines.append(f"- `{child_m}` **overrides** → `{parent_m}`")
    (docs_dir / "02-CALL-AND-TYPE-HIERARCHY.md").write_text("\n".join(ct_lines), encoding="utf-8")

    rt_lines = [f"# 03 — Cross-File References & Test Traceability (`{rname}`)\n", "[← 00-INDEX.md](./00-INDEX.md)\n",
                "| Production Symbol | Linked Tests |", "| :--- | :--- |"]
    for pid, tlist in list(bundle["test_map"].items())[:40]:
        rt_lines.append(f"| `{pid}` | {', '.join(f'`{t['test_id']}` ({t['link']})' for t in tlist[:4])} |")
    (docs_dir / "03-REFERENCES-AND-TESTS-MAP.md").write_text("\n".join(rt_lines), encoding="utf-8")

    kv_lines = [f"# 04 — KV-Cache Prefix Stability & PagedAttention Packing (`{rname}`)\n", "[← 00-INDEX.md](./00-INDEX.md)\n",
                "| KV Page | Used / Cap Tokens | Util % | Prefix SHA-256 | Packed AST Chunks |", "| :--- | :--- | :--- | :--- | :--- |"]
    for p in bundle["kv_pages"][:35]:
        c_list = ", ".join(f"`{c}`" for c in p["chunks"][:4]) + (f" (+{len(p['chunks'])-4})" if len(p["chunks"]) > 4 else "")
        kv_lines.append(f"| `page-{p['kv_page_id']:03d}` | `{p['used_tokens']}/{p['capacity_tokens']}` | `{p['utilization_pct']}%` | `{p['prefix_hash']}` | {c_list} |")
    (docs_dir / "04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md").write_text("\n".join(kv_lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="AST, Call/Type Hierarchy, Vectorless RAG & KV-Cache/PagedAttention Indexer")
    parser.add_argument("--repo", required=True, help="GitHub URL or local repository path")
    parser.add_argument("--output", required=True, help="Output directory for index/ and docs/")
    parser.add_argument("--page-size", type=int, default=512, help="PagedAttention virtual KV token page size")
    args = parser.parse_args()

    out_dir = Path(args.output).resolve()
    temp_clone = None
    try:
        if args.repo.startswith(("http://", "https://", "git@")):
            temp_clone = Path(tempfile.mkdtemp(prefix="ast_rag_"))
            repo_name = args.repo.rstrip("/").split("/")[-1].replace(".git", "")
            subprocess.run(["git", "clone", "--depth", "1", args.repo, str(temp_clone)], check=True)
            bundle = build_full_rag_index(temp_clone, repo_name, page_size=args.page_size)
        else:
            rpath = Path(args.repo).resolve()
            bundle = build_full_rag_index(rpath, rpath.name, page_size=args.page_size)
        write_outputs(bundle, out_dir)
        print(f"SUCCESS: Indexed {bundle['files_scanned']} files -> {len(bundle['chunks'])} AST chunks, {len(bundle['type_hierarchy'])} types, {len(bundle['kv_pages'])} KV pages in {out_dir}")
    finally:
        if temp_clone and temp_clone.exists():
            shutil.rmtree(temp_clone, ignore_errors=True)


if __name__ == "__main__":
    main()
