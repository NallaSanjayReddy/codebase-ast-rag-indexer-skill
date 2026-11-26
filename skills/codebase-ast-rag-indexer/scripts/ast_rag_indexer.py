#!/usr/bin/env python3
"""
Codebase AST, Knowledge Graph, Dual Vector + Vectorless RAG & KV-Cache/PagedAttention Indexer (v3.0).

Supports BOTH:
  - Vectorless RAG : Hierarchical PageIndex tree (tree_index.json), confidence-tagged Knowledge Graph
                     (graph.json: EXTRACTED/INFERRED/AMBIGUOUS), production-isolated subsystem
                     communities, God Nodes, import-cycle detection, rationale notes, graph.html.
  - Vector RAG     : Real dual embeddings (nlp_vector + code_vector) via pluggable providers
                     (zero-dependency offline TF-IDF subword projection, sentence-transformers,
                     OpenAI, or Ollama) stored in vectors.jsonl, SQLite (rag_index.sqlite),
                     Qdrant payload (qdrant_points.jsonl), and PostgreSQL pgvector_schema.sql.
  - Hybrid RRF     : Reciprocal Rank Fusion combining Vector Cosine + SQLite FTS5 BM25 + Graph signals.
  - KV-Cache / PA  : Prefix-stable canonical chunk packing into fixed-size PagedAttention token pages.

Zero external dependencies (pure Python 3 standard library).
"""
import argparse
import ast
import hashlib
import html
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA_VERSION = "3.0.0"

DEFAULT_SKIP_DIRS = {
    ".git", "node_modules", "target", "build", "dist", "out", ".gradle",
    ".idea", ".vscode", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    "vendor", ".next", ".nuxt", "coverage",
}

CODE_EXTS = {".py", ".java", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".kt", ".cs", ".php"}

LANG_FAMILY = {
    ".py": "python", ".java": "jvm", ".kt": "jvm",
    ".ts": "js", ".tsx": "js", ".js": "js", ".jsx": "js",
    ".go": "go", ".rs": "rust", ".cs": "dotnet", ".php": "php",
}

BUILTIN_NOISE = frozenset({
    "str", "int", "float", "bool", "bytes", "list", "dict", "set", "tuple", "object",
    "Exception", "ValueError", "TypeError", "KeyError", "RuntimeError", "Path", "Any",
    "Optional", "List", "Dict", "Set", "Tuple", "Union", "Callable", "Enum", "ABC",
    "Mock", "MagicMock", "AsyncMock", "TestCase", "String", "Integer", "Boolean",
    "Object", "Error", "Promise", "Array", "Record", "Map", "len", "print", "super",
    "isinstance", "getattr", "setattr", "hasattr", "range", "enumerate", "zip",
})

RATIONALE_RE = re.compile(r"(?:#|//)\s*(WHY|NOTE|ADR|DECISION|INVARIANT)\s*:\s*(.+)", re.IGNORECASE)


def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4.0))


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def tokenize_code_and_text(text: str) -> list[str]:
    """Identifier-aware tokenizer splitting camelCase, PascalCase, snake_case, and adding 3-grams."""
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+", text)
    tokens = []
    for tok in raw:
        # Split camelCase & snake_case
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", tok).lower().split("_")
        for p in parts:
            if len(p) >= 2:
                tokens.append(p)
                if len(p) >= 4:
                    for i in range(len(p) - 2):
                        tokens.append("3g:" + p[i:i + 3])
    return tokens


def embed_tfidf_batch(texts: list[str], dim: int = 128) -> tuple[list[list[float]], dict[str, float]]:
    """Zero-dependency deterministic dense L2-normalized TF-IDF hashed-projection embeddings."""
    doc_tokens = [tokenize_code_and_text(t) for t in texts]
    n_docs = max(1, len(doc_tokens))
    df = Counter()
    for toks in doc_tokens:
        for t in set(toks):
            df[t] += 1
    idf = {t: math.log((n_docs + 1.0) / (c + 1.0)) + 1.0 for t, c in df.items()}

    vectors = []
    for toks in doc_tokens:
        vec = [0.0] * dim
        tf = Counter(toks)
        total = max(1, len(toks))
        for tok, cnt in tf.items():
            w = (cnt / total) * idf.get(tok, 1.0)
            h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=8).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += sign * w
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-12:
            vec = [round(v / norm, 5) for v in vec]
        vectors.append(vec)
    return vectors, idf


def embed_texts(texts: list[str], provider: str = "tfidf", dim: int = 128, model: str = "") -> tuple[list[list[float]], int, dict]:
    """Pluggable embedding engine supporting offline TF-IDF, sentence-transformers, OpenAI, and Ollama."""
    if not texts or provider == "none":
        return [], 0, {}

    if provider == "tfidf":
        vecs, idf = embed_tfidf_batch(texts, dim=dim)
        return vecs, dim, {"idf_vocab_size": len(idf), "idf": idf}

    if provider == "sentence-transformers":
        from sentence_transformers import SentenceTransformer  # type: ignore
        m_name = model or "all-MiniLM-L6-v2"
        st = SentenceTransformer(m_name)
        arr = st.encode(texts, normalize_embeddings=True)
        vecs = [[round(float(x), 5) for x in row] for row in arr]
        return vecs, len(vecs[0]) if vecs else 384, {"model": m_name}

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for --embedding-provider openai")
        m_name = model or "text-embedding-3-small"
        vecs = []
        for i in range(0, len(texts), 64):
            batch = [t[:6000] for t in texts[i:i + 64]]
            req = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=json.dumps({"model": m_name, "input": batch}).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data["data"]:
                    vecs.append([round(float(x), 5) for x in item["embedding"]])
        return vecs, len(vecs[0]) if vecs else 1536, {"model": m_name}

    if provider == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        m_name = model or "nomic-embed-text"
        vecs = []
        for t in texts:
            req = urllib.request.Request(
                f"{host}/api/embeddings",
                data=json.dumps({"model": m_name, "prompt": t[:6000]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                vecs.append([round(float(x), 5) for x in data["embedding"]])
        return vecs, len(vecs[0]) if vecs else 768, {"model": m_name}

    raise ValueError(f"Unsupported embedding provider: {provider}")


def extract_rationale_notes(lines: list[str], start_line: int, end_line: int) -> list[dict]:
    notes = []
    lo = max(1, start_line - 3)
    hi = min(len(lines), end_line)
    for ln_no in range(lo, hi + 1):
        m = RATIONALE_RE.search(lines[ln_no - 1])
        if m:
            notes.append({"tag": m.group(1).upper(), "text": m.group(2).strip(), "line": ln_no})
    return notes


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
                if isinstance(sub.func, ast.Name):
                    calls.append((caller_id, sub.func.id, getattr(sub, "lineno", func_node.lineno), "EXTRACTED"))
                elif isinstance(sub.func, ast.Attribute):
                    calls.append((caller_id, sub.func.attr, getattr(sub, "lineno", func_node.lineno), "INFERRED"))

    def visit_block(body, parent_id=None, parent_class=None):
        for node in body:
            if isinstance(node, ast.ClassDef):
                cid = f"{mod_id}.{node.name}" if not parent_class else f"{parent_id}.{node.name}"
                bases = [get_ann(b) for b in node.bases if get_ann(b)]
                s_ln, e_ln = node.lineno, getattr(node, "end_lineno", node.lineno)
                code_slice = "\n".join(lines[s_ln - 1:e_ln])
                doc = ast.get_docstring(node) or ""
                symbols.append({
                    "id": cid, "name": node.name, "kind": "class", "language": "Python", "lang_family": "python",
                    "file": rel_path, "module": mod_id, "start_line": s_ln, "end_line": e_ln,
                    "parent_id": parent_id or mod_id, "parent_class": parent_class,
                    "signature": f"class {node.name}({', '.join(bases)}):" if bases else f"class {node.name}:",
                    "docstring": doc.splitlines()[0] if doc else "",
                    "rationale": extract_rationale_notes(lines, s_ln, e_ln),
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
                    "language": "Python", "lang_family": "python",
                    "file": rel_path, "module": mod_id, "start_line": s_ln, "end_line": e_ln,
                    "parent_id": parent_id or mod_id, "parent_class": parent_class,
                    "signature": sig, "docstring": doc.splitlines()[0] if doc else "",
                    "rationale": extract_rationale_notes(lines, s_ln, e_ln),
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
    lang_map = {
        ".java": "Java", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
        ".jsx": "JavaScript", ".go": "Go", ".rs": "Rust", ".kt": "Kotlin", ".cs": "C#", ".php": "PHP",
    }
    lang = lang_map.get(ext, "Code")
    lfam = LANG_FAMILY.get(ext, "code")
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
        r"(?:public|private|protected|static|async|export|func|fn|function|def|\s)+\s*"
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
                "id": cid, "name": cname, "kind": kind, "language": lang, "lang_family": lfam,
                "file": rel_path, "module": mod_id, "start_line": i + 1, "end_line": e_ln,
                "parent_id": mod_id, "parent_class": None,
                "signature": ln.strip().rstrip("{").strip(), "docstring": "",
                "rationale": extract_rationale_notes(lines, i + 1, e_ln),
                "super_types": supers, "param_types": [], "return_type": None,
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
                "id": fid, "name": fname, "kind": "method" if current_class else "function",
                "language": lang, "lang_family": lfam,
                "file": rel_path, "module": mod_id, "start_line": i + 1, "end_line": e_ln,
                "parent_id": current_class or mod_id,
                "parent_class": current_class.split(".")[-1] if current_class else None,
                "signature": ln.strip().rstrip("{").strip(), "docstring": "",
                "rationale": extract_rationale_notes(lines, i + 1, e_ln),
                "super_types": [], "param_types": [p.strip() for p in params_s.split(",") if p.strip()],
                "return_type": ts_ret or ret_t, "is_test": is_test or fname.lower().startswith("test"),
                "code": code_slice, "tokens": est_tokens(code_slice), "sha256": sha256_short(code_slice),
            })
            for call_m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", code_slice):
                if call_m.group(1) != fname and call_m.group(1) not in ("if", "for", "while", "switch", "catch", "new"):
                    calls.append((fid, call_m.group(1), i + 1, "INFERRED"))

    return symbols, calls, imports


def find_import_cycles(module_imports: dict[str, set[str]]) -> list[list[str]]:
    """Detect directed module import cycles."""
    visited, on_stack, stack = set(), set(), []
    cycles, seen_keys = [], set()

    def dfs(u: str):
        visited.add(u)
        on_stack.add(u)
        stack.append(u)
        for v in sorted(module_imports.get(u, ())):
            if v not in visited:
                dfs(v)
            elif v in on_stack:
                idx = stack.index(v)
                cyc = stack[idx:] + [v]
                key = tuple(sorted(cyc[:-1]))
                if key not in seen_keys and len(cyc) >= 3:
                    seen_keys.add(key)
                    cycles.append(cyc)
        stack.pop()
        on_stack.remove(u)

    for m in sorted(module_imports.keys()):
        if m not in visited:
            dfs(m)
    return cycles[:20]


def detect_communities(node_ids: list[str], edges: list[dict], node_meta: dict[str, dict]) -> tuple[dict[str, int], dict[int, dict]]:
    """
    Production-isolated label propagation community detection.
    Fixes test-pollution bug: test nodes never pull production symbols into a 'tests' community.
    """
    prod_ids = [nid for nid in node_ids if not node_meta[nid]["is_test"]]
    test_ids = [nid for nid in node_ids if node_meta[nid]["is_test"]]
    prod_set = set(prod_ids)

    adj = defaultdict(set)
    for e in edges:
        u, v = e["source"], e["target"]
        if u != v and u in prod_set and v in prod_set:
            adj[u].add(v)
            adj[v].add(u)

    labels = {}
    for nid in prod_ids:
        f = node_meta[nid]["file"]
        parts = f.split("/")
        # Use second-level subsystem when all code lives under a single root package (e.g. pgvector/psycopg)
        labels[nid] = "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) > 1 else "root")

    for _ in range(8):
        changed = False
        for nid in sorted(prod_ids):
            nbrs = adj.get(nid)
            if not nbrs:
                continue
            counts = Counter(labels[nb] for nb in nbrs if nb in labels)
            if not counts:
                continue
            best_label = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            if best_label != labels[nid]:
                labels[nid] = best_label
                changed = True
        if not changed:
            break

    groups = defaultdict(list)
    for nid, lbl in labels.items():
        groups[lbl].append(nid)
    if test_ids:
        groups["tests"].extend(test_ids)

    sorted_groups = sorted(groups.items(), key=lambda kv: (kv[0] == "tests", -len(kv[1]), kv[0]))
    node_to_cid, communities = {}, {}
    for cid, (lbl, members) in enumerate(sorted_groups):
        for m in members:
            node_to_cid[m] = cid
        internal_edges = sum(1 for e in edges if node_to_cid.get(e["source"]) == cid and node_to_cid.get(e["target"]) == cid)
        possible = max(1, len(members) * (len(members) - 1) / 2)
        communities[cid] = {
            "id": cid, "label": lbl, "size": len(members),
            "cohesion": round(min(1.0, internal_edges / possible), 3),
            "sample_nodes": members[:6],
        }
    return node_to_cid, communities


def build_nlp_text(chunk_meta: dict) -> str:
    parts = [
        f"{chunk_meta['language']} {chunk_meta['kind']} {chunk_meta['chunk_id']} in {chunk_meta['file']}.",
        f"Signature: {chunk_meta['signature']}.",
    ]
    if chunk_meta["docstring"]:
        parts.append(f"Summary: {chunk_meta['docstring']}")
    if chunk_meta["super_types"]:
        parts.append(f"Inherits/Implements: {', '.join(chunk_meta['super_types'])}.")
    if chunk_meta["super_implementation"]:
        parts.append(f"Overrides: {chunk_meta['super_implementation']}.")
    if chunk_meta["callers"]:
        parts.append(f"Called by: {', '.join(chunk_meta['callers'][:5])}.")
    if chunk_meta["callees"]:
        parts.append(f"Calls: {', '.join(chunk_meta['callees'][:5])}.")
    if chunk_meta["rationale"]:
        notes = "; ".join(f"{r['tag']}: {r['text']}" for r in chunk_meta["rationale"][:3])
        parts.append(f"Rationale: {notes}")
    return " ".join(parts)


def render_interactive_graph_html(repo_name: str, graph_data: dict) -> str:
    nodes_sorted = sorted(graph_data["nodes"], key=lambda n: (-n["degree"], n["id"]))[:180]
    keep_ids = {n["id"] for n in nodes_sorted}
    vis_edges = [e for e in graph_data["edges"] if e["source"] in keep_ids and e["target"] in keep_ids][:450]
    payload = json.dumps({
        "nodes": nodes_sorted, "edges": vis_edges, "communities": list(graph_data["communities"].values()),
    })
    safe_title = html.escape(repo_name)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{safe_title} — AST Knowledge Graph</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  body {{ background: #0d1117; color: #e6edf3; display: flex; height: 100vh; overflow: hidden; }}
  #sidebar {{ width: 320px; background: #161b22; border-right: 1px solid #30363d; padding: 16px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }}
  #sidebar h1 {{ font-size: 16px; color: #58a6ff; }}
  #search {{ width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: #e6edf3; font-size: 13px; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 4px; }}
  .EXTRACTED {{ background: #1f6feb33; color: #58a6ff; border: 1px solid #1f6feb; }}
  .INFERRED {{ background: #d2992233; color: #e3b341; border: 1px solid #d29922; }}
  .AMBIGUOUS {{ background: #f8514933; color: #ff7b72; border: 1px solid #f85149; }}
  #details {{ background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.5; }}
  #legend {{ display: flex; flex-wrap: wrap; gap: 6px; font-size: 11px; }}
  .leg-item {{ display: flex; align-items: center; gap: 4px; background: #0d1117; padding: 3px 6px; border-radius: 4px; border: 1px solid #30363d; }}
  .dot {{ width: 9px; height: 9px; border-radius: 50%; }}
  canvas {{ flex: 1; cursor: grab; }}
</style>
</head>
<body>
<div id="sidebar">
  <h1>{safe_title} — AST Graph</h1>
  <input id="search" placeholder="Filter symbol, file, or community..." />
  <div id="stats" style="font-size:12px;color:#8b949e;"></div>
  <div id="legend"></div>
  <div id="details">Click any node to inspect its AST signature, KV-Page, community, and confidence-tagged edges.</div>
</div>
<canvas id="canvas"></canvas>
<script>
const DATA = {payload};
const COLORS = ["#58a6ff","#3fb950","#d2a8ff","#ffa657","#ff7b72","#79c0ff","#56d364","#f2cc60","#a5d6ff","#e3b341"];
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let W = canvas.width = window.innerWidth - 320, H = canvas.height = window.innerHeight;
window.addEventListener("resize", () => {{ W = canvas.width = window.innerWidth - 320; H = canvas.height = window.innerHeight; }});
const nodes = DATA.nodes.map((n, i) => ({{ ...n, x: W/2 + Math.cos(i*0.7)*Math.min(W,H)*0.34, y: H/2 + Math.sin(i*0.7)*Math.min(W,H)*0.34, vx: 0, vy: 0, r: Math.max(5, Math.min(18, 4 + Math.sqrt(n.degree+1)*2.4)), color: COLORS[n.community % COLORS.length] }}));
const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
const edges = DATA.edges.filter(e => byId[e.source] && byId[e.target]);
document.getElementById("stats").textContent = `Showing ${{nodes.length}} nodes & ${{edges.length}} edges across ${{DATA.communities.length}} communities`;
const leg = document.getElementById("legend");
DATA.communities.slice(0, 12).forEach(c => {{ const el = document.createElement("div"); el.className = "leg-item"; el.innerHTML = `<span class="dot" style="background:${{COLORS[c.id % COLORS.length]}}"></span>${{c.label}} (${{c.size}})`; leg.appendChild(el); }});
let selected = null, filterText = "";
document.getElementById("search").addEventListener("input", e => {{ filterText = e.target.value.toLowerCase(); }});
canvas.addEventListener("click", e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  selected = nodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.r + 4) || null;
  if (selected) {{
    const inc = edges.filter(ed => ed.source === selected.id || ed.target === selected.id).slice(0, 14);
    const list = inc.map(ed => `<div><span class="badge ${{ed.confidence}}">${{ed.confidence}}</span><b>${{ed.relation}}</b> ${{ed.source === selected.id ? "→ " + ed.target : "← " + ed.source}}</div>`).join("");
    document.getElementById("details").innerHTML = `<div style="font-size:14px;font-weight:700;color:#58a6ff;margin-bottom:4px;">${{selected.id}}</div><div><b>Kind:</b> ${{selected.kind}} | <b>Degree:</b> ${{selected.degree}} | <b>KV-Page:</b> ${{selected.kv_page_id}}</div><div><b>File:</b> ${{selected.file}}:${{selected.line}}</div><div><b>Community:</b> #${{selected.community}} (${{selected.community_label}})</div><hr style="border-color:#30363d;margin:8px 0;"/>${{list || "<i>Isolated</i>"}}`;
  }}
}});
function step() {{
  for (let i = 0; i < nodes.length; i++) {{
    const a = nodes[i]; a.vx += (W/2 - a.x)*0.0012; a.vy += (H/2 - a.y)*0.0012;
    for (let j = i + 1; j < nodes.length; j++) {{
      const b = nodes[j], dx = a.x - b.x, dy = a.y - b.y, f = 900 / (dx*dx + dy*dy + 25);
      a.vx += dx*f*0.015; a.vy += dy*f*0.015; b.vx -= dx*f*0.015; b.vy -= dy*f*0.015;
    }}
  }}
  for (const e of edges) {{ const s = byId[e.source], t = byId[e.target], dx = t.x - s.x, dy = t.y - s.y; s.vx += dx*0.003; s.vy += dy*0.003; t.vx -= dx*0.003; t.vy -= dy*0.003; }}
  ctx.clearRect(0, 0, W, H);
  for (const e of edges) {{ const s = byId[e.source], t = byId[e.target]; ctx.strokeStyle = e.confidence === "EXTRACTED" ? "#58a6ff44" : (e.confidence === "AMBIGUOUS" ? "#f8514955" : "#e3b34133"); ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y); ctx.stroke(); }}
  for (const n of nodes) {{
    n.vx *= 0.86; n.vy *= 0.86; n.x = Math.max(20, Math.min(W-20, n.x + n.vx)); n.y = Math.max(20, Math.min(H-20, n.y + n.vy));
    const match = !filterText || n.id.toLowerCase().includes(filterText) || n.file.toLowerCase().includes(filterText) || n.community_label.toLowerCase().includes(filterText);
    ctx.globalAlpha = match ? 1.0 : 0.15; ctx.fillStyle = n === selected ? "#fff" : n.color;
    ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI*2); ctx.fill();
    if (n.degree >= 4 || n === selected || (filterText && match)) {{ ctx.fillStyle = "#e6edf3"; ctx.font = "11px sans-serif"; ctx.fillText(n.label, n.x + n.r + 3, n.y + 4); }}
    ctx.globalAlpha = 1.0;
  }}
  requestAnimationFrame(step);
}}
step();
</script>
</body>
</html>"""


def build_full_rag_index(
    repo_path: Path,
    repo_name: str,
    page_size: int = 512,
    chunk_strategy: str = "hybrid",
    rag_mode: str = "both",
    embedding_provider: str = "tfidf",
    embedding_dim: int = 128,
    embedding_model: str = "",
    priority_paths: list[str] | None = None,
    exclude_dirs: set[str] | None = None,
    prev_manifest: dict[str, str] | None = None,
):
    priority_paths = [p.strip().strip("/") for p in (priority_paths or []) if p.strip()]
    skip_dirs = DEFAULT_SKIP_DIRS | (exclude_dirs or set())

    all_symbols, raw_calls = [], []
    file_imports = defaultdict(list)
    file_manifest = {}
    files_scanned = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
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
            file_hash = sha256_short(source)
            file_manifest[rel_path] = file_hash

            if chunk_strategy == "file":
                mod_id = rel_path.replace("/", ".").removesuffix(ext)
                all_symbols.append({
                    "id": mod_id, "name": fpath.stem, "kind": "file", "language": ext.lstrip("."),
                    "lang_family": LANG_FAMILY.get(ext, "code"), "file": rel_path, "module": mod_id,
                    "start_line": 1, "end_line": max(1, len(source.splitlines())),
                    "parent_id": rel_path.split("/")[0] if "/" in rel_path else "root", "parent_class": None,
                    "signature": f"file {rel_path}", "docstring": "",
                    "rationale": extract_rationale_notes(source.splitlines(), 1, len(source.splitlines())),
                    "super_types": [], "param_types": [], "return_type": None, "is_test": is_test,
                    "code": source[:3000], "tokens": est_tokens(source[:3000]), "sha256": file_hash,
                })
                continue

            syms, cls, imps = (
                parse_python_file(rel_path, source, is_test)
                if ext == ".py"
                else parse_generic_file(rel_path, source, ext, is_test)
            )
            file_imports[rel_path].extend(imps)
            if chunk_strategy == "function":
                syms = [s for s in syms if s["kind"] in ("function", "method")]
            elif chunk_strategy == "class":
                syms = [s for s in syms if s["kind"] in ("class", "interface", "enum", "record", "struct", "trait")]

            all_symbols.extend(syms)
            raw_calls.extend(cls)

    prev_manifest = prev_manifest or {}
    delta = {
        "added": sorted(k for k in file_manifest if k not in prev_manifest),
        "modified": sorted(k for k in file_manifest if k in prev_manifest and prev_manifest[k] != file_manifest[k]),
        "unchanged": sorted(k for k in file_manifest if k in prev_manifest and prev_manifest[k] == file_manifest[k]),
        "deleted": sorted(k for k in prev_manifest if k not in file_manifest),
    }

    # Disambiguate duplicate symbol IDs (e.g. @overload, @property getter/setter)
    seen_ids = set()
    for s in all_symbols:
        base_id = s["id"]
        if base_id in seen_ids:
            s["id"] = f"{base_id}#L{s['start_line']}"
        seen_ids.add(s["id"])

    by_id = {s["id"]: s for s in all_symbols}
    by_name = defaultdict(list)
    by_module = defaultdict(list)
    class_methods = defaultdict(dict)
    for s in all_symbols:
        by_name[s["name"]].append(s["id"])
        by_module[s["module"]].append(s["id"])
        if s["kind"] == "method" and s.get("parent_class"):
            class_methods[s["parent_class"]][s["name"]] = s["id"]

    # Build module-level import graph & detect import cycles
    module_imports = defaultdict(set)
    file_imported_tokens = defaultdict(set)
    for rel_file, imps in file_imports.items():
        src_mod = rel_file.replace("/", ".").rsplit(".", 1)[0]
        for imp_name, _ in imps:
            cleaned = imp_name.strip().strip("'\"")
            file_imported_tokens[rel_file].add(cleaned)
            file_imported_tokens[rel_file].add(cleaned.split(".")[-1])
            for candidate_mod in by_module.keys():
                if candidate_mod != src_mod and (cleaned == candidate_mod or cleaned.startswith(candidate_mod + ".")):
                    module_imports[src_mod].add(candidate_mod)

    import_cycles = find_import_cycles(module_imports)

    outgoing_calls, incoming_calls = defaultdict(set), defaultdict(set)
    references = defaultdict(list)
    graph_edges, seen_edges = [], set()

    def add_edge(src: str, tgt: str, relation: str, confidence: str, line: int = 0):
        if src == tgt or src not in by_id or tgt not in by_id:
            return
        key = (src, tgt, relation)
        if key not in seen_edges:
            seen_edges.add(key)
            graph_edges.append({
                "source": src, "target": tgt, "relation": relation, "confidence": confidence, "line": line,
            })

    # Add same-language-family & import-constrained call edges (fixes cross-language & bare-name ambiguity)
    for caller_id, callee_name, line, base_conf in raw_calls:
        if caller_id not in by_id:
            continue
        caller = by_id[caller_id]
        caller_file = caller["file"]
        caller_fam = caller["lang_family"]
        candidates = [tid for tid in by_name.get(callee_name, []) if tid != caller_id and by_id[tid]["lang_family"] == caller_fam]
        if not candidates:
            continue

        # Prefer same-file or explicitly imported targets (EXTRACTED) over bare-name fallback
        imp_toks = file_imported_tokens.get(caller_file, set())
        imported_matches = [
            tid for tid in candidates
            if by_id[tid]["file"] == caller_file
            or by_id[tid]["module"] in imp_toks
            or any(tid.startswith(tok) for tok in imp_toks if "." in tok)
        ]
        if imported_matches:
            selected = imported_matches[:2]
            conf = "EXTRACTED" if len(imported_matches) == 1 else "INFERRED"
        else:
            selected = candidates[:3]
            conf = "AMBIGUOUS" if len(candidates) > 2 else base_conf

        for tid in selected:
            outgoing_calls[caller_id].add(tid)
            incoming_calls[tid].add(caller_id)
            references[tid].append({"from_symbol": caller_id, "file": caller_file, "line": line, "kind": "call", "confidence": conf})
            add_edge(caller_id, tid, "calls", conf, line)

    type_hierarchy, sub_types = {}, defaultdict(list)
    super_impls, type_defs = {}, defaultdict(list)
    for s in all_symbols:
        if s["kind"] in ("class", "interface", "enum", "record", "struct", "trait"):
            resolved_supers = []
            for st in s["super_types"]:
                matched = [mid for mid in by_name.get(st.split(".")[-1], []) if by_id[mid]["lang_family"] == s["lang_family"]]
                if matched:
                    conf = "EXTRACTED" if len(matched) == 1 else "AMBIGUOUS"
                    for mid in matched[:2]:
                        resolved_supers.append(mid)
                        sub_types[mid].append(s["id"])
                        references[mid].append({"from_symbol": s["id"], "file": s["file"], "line": s["start_line"], "kind": "extends/implements", "confidence": conf})
                        add_edge(s["id"], mid, "inherits", conf, s["start_line"])
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
                    parent_m = class_methods[sup_name][s["name"]]
                    super_impls[s["id"]] = parent_m
                    add_edge(s["id"], parent_m, "overrides", "INFERRED", s["start_line"])
        for ann in list(s.get("param_types", [])) + ([s["return_type"]] if s.get("return_type") else []):
            for tok in re.findall(r"\b([A-Z][A-Za-z0-9_]+)\b", str(ann)):
                for td_id in by_name.get(tok, [])[:2]:
                    if by_id[td_id]["lang_family"] == s["lang_family"] and td_id not in type_defs[s["id"]]:
                        type_defs[s["id"]].append(td_id)
                        add_edge(s["id"], td_id, "uses_type", "EXTRACTED", s["start_line"])

    test_map = defaultdict(list)
    for ts in [s for s in all_symbols if s["is_test"]]:
        for callee_id in outgoing_calls.get(ts["id"], []):
            if not by_id[callee_id]["is_test"]:
                test_map[callee_id].append({"test_id": ts["id"], "file": ts["file"], "line": ts["start_line"], "link": "direct_call"})
                add_edge(ts["id"], callee_id, "tests", "EXTRACTED", ts["start_line"])
        low_t = ts["name"].lower()
        for prod_name, prod_ids in by_name.items():
            if len(prod_name) >= 4 and prod_name.lower() in low_t:
                for pid in prod_ids[:2]:
                    if not by_id[pid]["is_test"] and by_id[pid]["lang_family"] == ts["lang_family"]:
                        entry = {"test_id": ts["id"], "file": ts["file"], "line": ts["start_line"], "link": "name_match"}
                        if entry not in test_map[pid]:
                            test_map[pid].append(entry)
                            add_edge(ts["id"], pid, "tests", "INFERRED", ts["start_line"])

    def is_priority(rel_file: str) -> bool:
        return any(rel_file.startswith(p + "/") or rel_file == p for p in priority_paths)

    canonical_symbols = sorted(
        all_symbols,
        key=lambda s: (s["is_test"], not is_priority(s["file"]), s["file"], s["start_line"], s["id"]),
    )

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
        ch = {
            "chunk_id": s["id"], "name": s["name"], "kind": s["kind"], "language": s["language"],
            "file": s["file"], "start_line": s["start_line"], "end_line": s["end_line"],
            "parent_id": s["parent_id"], "signature": s["signature"], "docstring": s["docstring"],
            "rationale": s["rationale"], "priority_boost": 2.0 if is_priority(s["file"]) else 1.0,
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
        }
        ch["nlp_text"] = build_nlp_text(ch)
        ch["code_text"] = ch["code"]
        chunks.append(ch)

    if cur_page["chunks"]:
        cur_page["prefix_hash"] = sha256_short("|".join(cur_page["chunks"]))
        cur_page["utilization_pct"] = round(cur_page["used_tokens"] * 100.0 / page_size, 1)
        kv_pages.append(cur_page)

    degree = Counter()
    for e in graph_edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1

    chunk_by_id = {c["chunk_id"]: c for c in chunks}
    node_ids = [c["chunk_id"] for c in chunks]
    node_to_cid, communities = detect_communities(node_ids, graph_edges, chunk_by_id)

    graph_nodes = []
    for c in chunks:
        cid = node_to_cid.get(c["chunk_id"], 0)
        c["community_id"] = cid
        c["community_label"] = communities[cid]["label"] if cid in communities else "root"
        c["degree"] = degree[c["chunk_id"]]
        graph_nodes.append({
            "id": c["chunk_id"], "label": c["name"], "kind": c["kind"],
            "file": c["file"], "line": c["start_line"], "kv_page_id": c["kv_page_id"],
            "degree": c["degree"], "community": cid, "community_label": c["community_label"],
            "is_test": c["is_test"],
        })

    god_nodes = [
        {"id": n["id"], "label": n["label"], "kind": n["kind"], "file": n["file"], "degree": n["degree"], "community": n["community_label"]}
        for n in sorted(graph_nodes, key=lambda x: (-x["degree"], x["id"]))
        if not n["is_test"] and n["label"] not in BUILTIN_NOISE and n["degree"] > 0
    ][:12]

    surprising_bridges = []
    for e in graph_edges:
        c_src, c_tgt = node_to_cid.get(e["source"]), node_to_cid.get(e["target"])
        if c_src is not None and c_tgt is not None and c_src != c_tgt:
            if not chunk_by_id[e["source"]]["is_test"] and not chunk_by_id[e["target"]]["is_test"]:
                surprising_bridges.append({
                    "source": e["source"], "source_community": communities[c_src]["label"],
                    "target": e["target"], "target_community": communities[c_tgt]["label"],
                    "relation": e["relation"], "confidence": e["confidence"],
                })
    surprising_bridges = surprising_bridges[:25]

    conf_counts = Counter(e["confidence"] for e in graph_edges)
    graph_data = {
        "schema_version": SCHEMA_VERSION, "repo": repo_name,
        "stats": {
            "nodes": len(graph_nodes), "edges": len(graph_edges),
            "communities": len(communities), "import_cycles": len(import_cycles),
            "confidence_breakdown": dict(conf_counts),
        },
        "god_nodes": god_nodes, "surprising_bridges": surprising_bridges,
        "import_cycles": import_cycles, "communities": communities,
        "nodes": graph_nodes, "edges": graph_edges,
    }

    tree_index = {"repo": repo_name, "schema_version": SCHEMA_VERSION, "total_files": files_scanned, "total_symbols": len(chunks), "modules": {}}
    for c in chunks:
        mod = c["file"].split("/")[0] if "/" in c["file"] else "root"
        mod_node = tree_index["modules"].setdefault(mod, {"files": {}, "symbol_count": 0, "total_tokens": 0})
        mod_node["symbol_count"] += 1
        mod_node["total_tokens"] += c["token_count"]
        f_node = mod_node["files"].setdefault(c["file"], {"symbols": []})
        f_node["symbols"].append({
            "id": c["chunk_id"], "kind": c["kind"], "signature": c["signature"],
            "lines": f"{c['start_line']}-{c['end_line']}", "kv_page_id": c["kv_page_id"],
            "community": c["community_id"], "community_label": c["community_label"], "degree": c["degree"],
            "callers": len(c["callers"]), "callees": len(c["callees"]), "tests": len(c["tests"]),
        })

    # Build real dual vectors when rag_mode includes vector ("both" or "vector")
    vector_bundle = {"enabled": False, "provider": "none", "dim": 0, "records": [], "idf": {}}
    if rag_mode in ("both", "vector") and embedding_provider != "none" and chunks:
        nlp_vecs, actual_dim, nlp_meta = embed_texts(
            [c["nlp_text"] for c in chunks], provider=embedding_provider, dim=embedding_dim, model=embedding_model
        )
        code_vecs, _, _ = embed_texts(
            [c["code_text"] for c in chunks], provider=embedding_provider, dim=embedding_dim, model=embedding_model
        )
        records = []
        for c, nv, cv in zip(chunks, nlp_vecs, code_vecs):
            records.append({
                "chunk_id": c["chunk_id"], "file": c["file"], "kind": c["kind"],
                "priority_boost": c["priority_boost"], "kv_page_id": c["kv_page_id"],
                "community_label": c["community_label"], "degree": c["degree"],
                "nlp_vector": nv, "code_vector": cv,
            })
        vector_bundle = {
            "enabled": True, "provider": embedding_provider, "dim": actual_dim,
            "model": nlp_meta.get("model", embedding_provider),
            "records": records, "idf": nlp_meta.get("idf", {}),
        }

    return {
        "repo_name": repo_name, "files_scanned": files_scanned, "chunk_strategy": chunk_strategy,
        "rag_mode": rag_mode, "priority_paths": priority_paths, "file_manifest": file_manifest, "delta": delta,
        "chunks": chunks, "tree_index": tree_index, "graph": graph_data, "vectors": vector_bundle,
        "call_graph": {"outgoing": {k: sorted(v) for k, v in outgoing_calls.items()},
                       "incoming": {k: sorted(v) for k, v in incoming_calls.items()}},
        "type_hierarchy": type_hierarchy, "super_implementations": super_impls,
        "type_definitions": dict(type_defs), "references": dict(references),
        "test_map": dict(test_map), "kv_pages": kv_pages, "page_size": page_size,
    }


def write_sqlite_store(chunks: list[dict], vector_bundle: dict, db_path: Path):
    """Build local zero-server SQLite FTS5 + Dual-Vector store."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE chunk_meta (
                chunk_id TEXT PRIMARY KEY, name TEXT, kind TEXT, file TEXT,
                start_line INT, end_line INT, kv_page_id INT, priority_boost REAL,
                community_label TEXT, degree INT, signature TEXT
            )
        """)
        cur.execute("""
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                chunk_id UNINDEXED, name, signature, nlp_text, code_text,
                tokenize='porter unicode61'
            )
        """)
        cur.execute("""
            CREATE TABLE chunk_vectors (
                chunk_id TEXT PRIMARY KEY, provider TEXT, dim INT,
                nlp_vector TEXT, code_vector TEXT
            )
        """)
        for c in chunks:
            cur.execute(
                "INSERT OR REPLACE INTO chunk_meta VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (c["chunk_id"], c["name"], c["kind"], c["file"], c["start_line"], c["end_line"],
                 c["kv_page_id"], c["priority_boost"], c["community_label"], c["degree"], c["signature"]),
            )
            cur.execute(
                "INSERT INTO chunks_fts VALUES (?,?,?,?,?)",
                (c["chunk_id"], c["name"], c["signature"], c["nlp_text"], c["code_text"]),
            )
        if vector_bundle.get("enabled"):
            for r in vector_bundle["records"]:
                cur.execute(
                    "INSERT OR REPLACE INTO chunk_vectors VALUES (?,?,?,?,?)",
                    (r["chunk_id"], vector_bundle["provider"], vector_bundle["dim"],
                     json.dumps(r["nlp_vector"]), json.dumps(r["code_vector"])),
                )
        conn.commit()
    finally:
        conn.close()


def write_outputs(bundle: dict, out_dir: Path, output_format: str = "full"):
    idx_dir, docs_dir = out_dir / "index", out_dir / "docs"
    idx_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    (idx_dir / "file_manifest.json").write_text(json.dumps(bundle["file_manifest"], indent=2), encoding="utf-8")
    with (idx_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for ch in bundle["chunks"]:
            f.write(json.dumps(ch) + "\n")

    if output_format == "chunks":
        return

    # Vectorless RAG artifacts
    if bundle["rag_mode"] in ("both", "vectorless"):
        (idx_dir / "tree_index.json").write_text(json.dumps(bundle["tree_index"], indent=2), encoding="utf-8")
        (idx_dir / "graph.json").write_text(json.dumps(bundle["graph"], indent=2), encoding="utf-8")
        (idx_dir / "call_graph.json").write_text(json.dumps(bundle["call_graph"], indent=2), encoding="utf-8")
        (idx_dir / "type_hierarchy.json").write_text(json.dumps({
            "types": bundle["type_hierarchy"],
            "super_implementations": bundle["super_implementations"],
            "type_definitions": bundle["type_definitions"],
        }, indent=2), encoding="utf-8")
        (idx_dir / "references.json").write_text(json.dumps(bundle["references"], indent=2), encoding="utf-8")
        (idx_dir / "test_map.json").write_text(json.dumps(bundle["test_map"], indent=2), encoding="utf-8")
        (docs_dir / "graph.html").write_text(render_interactive_graph_html(bundle["repo_name"], bundle["graph"]), encoding="utf-8")

    (idx_dir / "kv_paged_blocks.json").write_text(json.dumps({
        "page_size_tokens": bundle["page_size"], "total_pages": len(bundle["kv_pages"]), "pages": bundle["kv_pages"],
    }, indent=2), encoding="utf-8")

    # Vector RAG artifacts
    vbundle = bundle["vectors"]
    if vbundle.get("enabled"):
        (idx_dir / "vector_meta.json").write_text(json.dumps({
            "schema_version": SCHEMA_VERSION, "provider": vbundle["provider"],
            "model": vbundle["model"], "dim": vbundle["dim"], "total_vectors": len(vbundle["records"]),
            "idf": vbundle["idf"],
        }), encoding="utf-8")
        with (idx_dir / "vectors.jsonl").open("w", encoding="utf-8") as vf:
            for r in vbundle["records"]:
                vf.write(json.dumps(r) + "\n")
        # Qdrant-ready export
        with (idx_dir / "qdrant_points.jsonl").open("w", encoding="utf-8") as qf:
            for idx_num, r in enumerate(vbundle["records"], 1):
                qf.write(json.dumps({
                    "id": idx_num,
                    "vector": {"nlp": r["nlp_vector"], "code": r["code_vector"]},
                    "payload": {
                        "chunk_id": r["chunk_id"], "file": r["file"], "kind": r["kind"],
                        "community": r["community_label"], "kv_page_id": r["kv_page_id"],
                        "priority_boost": r["priority_boost"],
                    },
                }) + "\n")

    write_sqlite_store(bundle["chunks"], vbundle, idx_dir / "rag_index.sqlite")

    vec_dim = vbundle["dim"] if vbundle.get("enabled") else 1536
    (idx_dir / "pgvector_schema.sql").write_text(f"""-- PostgreSQL pgvector 0.8+ Dual-Embedding Hybrid AST RAG Schema (dim={vec_dim})
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_ast_chunks (
    chunk_id TEXT PRIMARY KEY,
    repo_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    kind TEXT NOT NULL,
    signature TEXT NOT NULL,
    parent_id TEXT,
    start_line INT NOT NULL,
    end_line INT NOT NULL,
    kv_page_id INT NOT NULL,
    community_id INT NOT NULL DEFAULT 0,
    degree INT NOT NULL DEFAULT 0,
    priority_boost REAL NOT NULL DEFAULT 1.0,
    token_count INT NOT NULL,
    sha256 TEXT NOT NULL,
    callers JSONB NOT NULL DEFAULT '[]'::jsonb,
    callees JSONB NOT NULL DEFAULT '[]'::jsonb,
    super_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    super_implementation TEXT,
    tests JSONB NOT NULL DEFAULT '[]'::jsonb,
    nlp_text TEXT NOT NULL,
    code_text TEXT NOT NULL,
    fts TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', signature || ' ' || nlp_text || ' ' || code_text)) STORED,
    nlp_embedding HALFVEC({vec_dim}),
    code_embedding HALFVEC({vec_dim})
);

CREATE INDEX IF NOT EXISTS idx_ast_chunks_nlp_hnsw  ON code_ast_chunks USING hnsw (nlp_embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_code_hnsw ON code_ast_chunks USING hnsw (code_embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_fts       ON code_ast_chunks USING gin (fts);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_page      ON code_ast_chunks (repo_name, kv_page_id);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_comm      ON code_ast_chunks (repo_name, community_id);
""", encoding="utf-8")

    if output_format == "metadata":
        return

    rname = bundle["repo_name"]
    n_pages = len(bundle["kv_pages"])
    avg_util = round(sum(p["utilization_pct"] for p in bundle["kv_pages"]) / max(1, n_pages), 1)
    gstats = bundle["graph"]["stats"]
    conf = gstats["confidence_breakdown"]
    vec_desc = f"`{vbundle['provider']}` (`dim={vbundle['dim']}`, `{len(vbundle['records'])}` dual vectors)" if vbundle.get("enabled") else "`disabled (vectorless-only)`"

    (docs_dir / "00-INDEX.md").write_text(f"""# {rname} — Dual Vector & Vectorless AST RAG Index (`v{SCHEMA_VERSION}`)

| Metric | Value |
| :--- | :--- |
| **RAG Mode / Chunk Strategy** | `{bundle["rag_mode"]}` / `{bundle["chunk_strategy"]}` |
| **Vector Embeddings (`vectors.jsonl` + SQLite + Qdrant)** | {vec_desc} |
| **Source Files Scanned** | `{bundle["files_scanned"]}` |
| **AST Symbol Chunks (`chunks.jsonl` + `rag_index.sqlite`)** | `{len(bundle["chunks"])}` |
| **Knowledge Graph Edges (`graph.json`)** | `{gstats["edges"]}` (`EXTRACTED={conf.get("EXTRACTED", 0)}`, `INFERRED={conf.get("INFERRED", 0)}`, `AMBIGUOUS={conf.get("AMBIGUOUS", 0)}`) |
| **Production Subsystem Communities / Import Cycles** | `{gstats["communities"]}` communities / `{gstats["import_cycles"]}` cycles |
| **Types Mapped / Super-Implementations** | `{len(bundle["type_hierarchy"])}` types / `{len(bundle["super_implementations"])}` overrides |
| **Production Symbols Linked to Tests** | `{len(bundle["test_map"])}` |
| **PagedAttention KV Pages (`{bundle["page_size"]}` tok/page)** | `{n_pages}` (`{avg_util}%` avg utilization) |

## Indexed Documentation & Interactive Graph
- **[`01-TREE-INDEX-VECTORLESS-RAG.md`](./01-TREE-INDEX-VECTORLESS-RAG.md)** — PageIndex hierarchical tree for Vectorless RAG
- **[`02-CALL-AND-TYPE-HIERARCHY.md`](./02-CALL-AND-TYPE-HIERARCHY.md)** — Callers, callees, supertypes, subtypes & super-implementations
- **[`03-REFERENCES-AND-TESTS-MAP.md`](./03-REFERENCES-AND-TESTS-MAP.md)** — Cross-file references & production-to-test traceability
- **[`04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md`](./04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md)** — KV-cache prefix blocks, PagedAttention virtual pages & dual-embedding `pgvector`/Qdrant stores
- **[`05-GRAPH-REPORT.md`](./05-GRAPH-REPORT.md)** — God Nodes, Subsystem Communities, Surprising Cross-Community Bridges, Import Cycles & Rationale Notes
- **[`graph.html`](./graph.html)** — Self-contained interactive force-directed knowledge graph viewer
""", encoding="utf-8")

    tree_lines = [f"# 01 — Vectorless RAG Tree Index (`{rname}`)\n", "[← 00-INDEX.md](./00-INDEX.md)\n"]
    for mod, mdata in sorted(bundle["tree_index"]["modules"].items()):
        tree_lines.append(f"## Module `{mod}` ({mdata['symbol_count']} symbols, ~{mdata['total_tokens']:,} tokens)")
        for fpath, fdata in sorted(mdata["files"].items())[:25]:
            tree_lines.append(f"- **`{fpath}`**")
            for sym in fdata["symbols"][:12]:
                tree_lines.append(f"  - `{sym['kind']}` **`{sym['id']}`** (L{sym['lines']}, KV-Page `{sym['kv_page_id']}`, Comm `{sym['community_label']}`, deg=`{sym['degree']}`, callers=`{sym['callers']}`, callees=`{sym['callees']}`, tests=`{sym['tests']}`)")
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

    gr_lines = [
        f"# 05 — Knowledge Graph Report (`{rname}`)\n",
        "[← 00-INDEX.md](./00-INDEX.md) | [Interactive Graph (`graph.html`)](./graph.html)\n",
        "## God Nodes (Most-Connected Core Abstractions)\n",
        "| Symbol | Kind | Community | Degree | File |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for gn in bundle["graph"]["god_nodes"]:
        gr_lines.append(f"| `{gn['id']}` | {gn['kind']} | `{gn['community']}` | `{gn['degree']}` | `{gn['file']}` |")
    gr_lines.append("\n## Detected Subsystem Communities (Production-Isolated)\n")
    gr_lines.append("| Community | Label | Symbols | Cohesion | Sample Nodes |")
    gr_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for cinfo in list(bundle["graph"]["communities"].values())[:20]:
        samps = ", ".join(f"`{x.split('.')[-1]}`" for x in cinfo["sample_nodes"][:4])
        gr_lines.append(f"| `#{cinfo['id']}` | `{cinfo['label']}` | `{cinfo['size']}` | `{cinfo['cohesion']}` | {samps} |")
    gr_lines.append("\n## Surprising Cross-Community Bridges\n")
    if bundle["graph"]["surprising_bridges"]:
        for b in bundle["graph"]["surprising_bridges"][:15]:
            gr_lines.append(f"- `{b['source']}` (`{b['source_community']}`) **`--{b['relation']}-->`** `{b['target']}` (`{b['target_community']}`) [`{b['confidence']}`]")
    else:
        gr_lines.append("- *No cross-community bridges detected.*")

    gr_lines.append("\n## Import Cycles\n")
    if bundle["graph"]["import_cycles"]:
        for cyc in bundle["graph"]["import_cycles"]:
            gr_lines.append(f"- `{' -> '.join(cyc)}`")
    else:
        gr_lines.append("- *No module import cycles detected.*")

    rationale_items = [(c["chunk_id"], r) for c in bundle["chunks"] for r in c.get("rationale", [])]
    gr_lines.append(f"\n## Extracted Rationale & Design Notes (`{len(rationale_items)}` found)\n")
    for cid, r in rationale_items[:20]:
        gr_lines.append(f"- **`[{r['tag']}]`** `{cid}` (L{r['line']}): {r['text']}")
    if not rationale_items:
        gr_lines.append("- *No `# WHY:` / `# NOTE:` / `// ADR:` rationale comments found.*")

    delta = bundle["delta"]
    gr_lines.append(f"\n## Incremental File Manifest Delta\n- Added: `{len(delta['added'])}` | Modified: `{len(delta['modified'])}` | Unchanged: `{len(delta['unchanged'])}` | Deleted: `{len(delta['deleted'])}`\n")
    (docs_dir / "05-GRAPH-REPORT.md").write_text("\n".join(gr_lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Dual Vector + Vectorless AST RAG & KV-Cache/PagedAttention Indexer (v3.0)")
    parser.add_argument("--repo", required=True, help="GitHub URL or local repository path")
    parser.add_argument("--output", required=True, help="Output directory for index/ and docs/")
    parser.add_argument("--page-size", type=int, default=512, help="PagedAttention virtual KV token page size")
    parser.add_argument("--chunk-strategy", choices=["hybrid", "function", "class", "file"], default="hybrid")
    parser.add_argument("--rag-mode", choices=["both", "vectorless", "vector"], default="both", help="Build vectorless, vector, or both RAG indexes")
    parser.add_argument("--embedding-provider", choices=["tfidf", "sentence-transformers", "openai", "ollama", "none"], default="tfidf")
    parser.add_argument("--embedding-dim", type=int, default=128, help="Dense dimension for offline TF-IDF vector projection")
    parser.add_argument("--embedding-model", default="", help="Optional model override for sentence-transformers/openai/ollama")
    parser.add_argument("--output-format", choices=["full", "chunks", "metadata"], default="full")
    parser.add_argument("--priority-paths", default="", help="Comma-separated directory prefixes to boost in retrieval")
    parser.add_argument("--exclude-dirs", default="", help="Comma-separated extra directory names to exclude")
    parser.add_argument("--incremental", action="store_true", help="Compare against previous index/file_manifest.json")
    args = parser.parse_args()

    out_dir = Path(args.output).resolve()
    prev_manifest = None
    manifest_file = out_dir / "index" / "file_manifest.json"
    if args.incremental and manifest_file.exists():
        try:
            prev_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            prev_manifest = None

    priority_paths = [p.strip() for p in args.priority_paths.split(",") if p.strip()]
    exclude_dirs = {d.strip() for d in args.exclude_dirs.split(",") if d.strip()}

    temp_clone = None
    try:
        if args.repo.startswith(("http://", "https://", "git@")):
            temp_clone = Path(tempfile.mkdtemp(prefix="ast_rag_"))
            repo_name = args.repo.rstrip("/").split("/")[-1].replace(".git", "")
            subprocess.run(["git", "clone", "--depth", "1", args.repo, str(temp_clone)], check=True)
            bundle = build_full_rag_index(
                temp_clone, repo_name, page_size=args.page_size, chunk_strategy=args.chunk_strategy,
                rag_mode=args.rag_mode, embedding_provider=args.embedding_provider,
                embedding_dim=args.embedding_dim, embedding_model=args.embedding_model,
                priority_paths=priority_paths, exclude_dirs=exclude_dirs, prev_manifest=prev_manifest,
            )
        else:
            rpath = Path(args.repo).resolve()
            bundle = build_full_rag_index(
                rpath, rpath.name, page_size=args.page_size, chunk_strategy=args.chunk_strategy,
                rag_mode=args.rag_mode, embedding_provider=args.embedding_provider,
                embedding_dim=args.embedding_dim, embedding_model=args.embedding_model,
                priority_paths=priority_paths, exclude_dirs=exclude_dirs, prev_manifest=prev_manifest,
            )
        write_outputs(bundle, out_dir, output_format=args.output_format)
        gstats = bundle["graph"]["stats"]
        vinfo = f"{len(bundle['vectors']['records'])} dual vectors ({bundle['vectors']['provider']} d={bundle['vectors']['dim']})" if bundle["vectors"]["enabled"] else "vectorless-only"
        print(
            f"SUCCESS: Indexed {bundle['files_scanned']} files -> {len(bundle['chunks'])} AST chunks, "
            f"{vinfo}, {gstats['edges']} graph edges ({gstats['communities']} communities), "
            f"{len(bundle['kv_pages'])} KV pages in {out_dir}"
        )
    finally:
        if temp_clone and temp_clone.exists():
            shutil.rmtree(temp_clone, ignore_errors=True)


if __name__ == "__main__":
    main()
