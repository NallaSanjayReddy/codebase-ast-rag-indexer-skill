#!/usr/bin/env python3
"""
Generates two publication-grade README visual assets for codebase-ast-rag-indexer-skill:
  1. assets/workflow_overview.gif  (1440x960, dense Excalidraw-style pastel-zone animated workflow)
  2. assets/setup_walkthrough.mp4  (1280x720, 24fps H.264 setup & CLI walkthrough video)
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
OUT_GIF = ASSETS / "workflow_overview.gif"
OUT_MP4 = ASSETS / "setup_walkthrough.mp4"


def load_font(size: int, bold: bool = False, mono: bool = False):
    cands = (
        ["C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"]
        if mono
        else ["C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
              "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"]
    )
    for p in cands:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# Fonts
F_H1 = load_font(26, bold=True)
F_ZONE = load_font(17, bold=True)
F_SUBH = load_font(13, bold=True)
F_BODY = load_font(12, bold=False)
F_TINY = load_font(11, bold=False)
F_MONO = load_font(11, bold=True, mono=True)
F_TERM_H = load_font(22, bold=True)
F_TERM = load_font(15, bold=False, mono=True)
F_TERM_B = load_font(15, bold=True, mono=True)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2


def draw_dashed_rounded_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline, width: int = 3, dash: int = 10, gap: int = 6):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill)
    # Top & bottom dashed edges
    for x in range(x0 + radius, x1 - radius, dash + gap):
        ex = min(x + dash, x1 - radius)
        draw.line([(x, y0), (ex, y0)], fill=outline, width=width)
        draw.line([(x, y1), (ex, y1)], fill=outline, width=width)
    # Left & right dashed edges
    for y in range(y0 + radius, y1 - radius, dash + gap):
        ey = min(y + dash, y1 - radius)
        draw.line([(x0, y), (x0, ey)], fill=outline, width=width)
        draw.line([(x1, y), (x1, ey)], fill=outline, width=width)
    # Corner arcs
    d = radius * 2
    draw.arc([x0, y0, x0 + d, y0 + d], 180, 270, fill=outline, width=width)
    draw.arc([x1 - d, y0, x1, y0 + d], 270, 360, fill=outline, width=width)
    draw.arc([x0, y1 - d, x0 + d, y1], 90, 180, fill=outline, width=width)
    draw.arc([x1 - d, y1 - d, x1, y1], 0, 90, fill=outline, width=width)


def draw_dashed_line(draw: ImageDraw.ImageDraw, p0, p1, color, width: int = 2, dash: int = 7, gap: int = 5):
    x0, y0 = p0
    x1, y1 = p1
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist < 1:
        return
    steps = int(dist / (dash + gap)) + 1
    for i in range(steps):
        t0 = (i * (dash + gap)) / dist
        t1 = min(1.0, (i * (dash + gap) + dash) / dist)
        if t0 >= 1.0:
            break
        draw.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                   (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=color, width=width)


def draw_arrow(draw: ImageDraw.ImageDraw, p0, p1, color, width: int = 3):
    draw.line([p0, p1], fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ahl = 10
    left = (p1[0] - ahl * math.cos(ang - 0.45), p1[1] - ahl * math.sin(ang - 0.45))
    right = (p1[0] - ahl * math.cos(ang + 0.45), p1[1] - ahl * math.sin(ang + 0.45))
    draw.polygon([p1, left, right], fill=color)


def draw_cylinder_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int, h: int, fill, outline, label: str = ""):
    rx, ry = w // 2, 8
    ty, by = cy - h // 2 + ry, cy + h // 2 - ry
    draw.rectangle([cx - rx, ty, cx + rx, by], fill=fill)
    draw.ellipse([cx - rx, by - ry, cx + rx, by + ry], fill=fill, outline=outline, width=2)
    draw.line([(cx - rx, ty), (cx - rx, by)], fill=outline, width=2)
    draw.line([(cx + rx, ty), (cx + rx, by)], fill=outline, width=2)
    draw.ellipse([cx - rx, ty - ry, cx + rx, ty + ry], fill=fill, outline=outline, width=2)
    if label:
        draw.text((cx - len(label) * 3 - 2, cy - 4), label, fill=outline, font=F_MONO)


def draw_graph_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill, outline):
    draw.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=8, fill=fill, outline=outline, width=2)
    pts = [(cx - 10, cy - 9), (cx + 11, cy - 7), (cx, cy + 1), (cx - 11, cy + 10), (cx + 10, cy + 9)]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if (i + j) % 2 == 1:
                draw.line([pts[i], pts[j]], fill=outline, width=1)
    for px, py in pts:
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=outline)


def draw_funnel_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, fill, outline):
    pts = [(cx - 18, cy - 14), (cx + 18, cy - 14), (cx + 5, cy + 2), (cx + 5, cy + 16), (cx - 5, cy + 12), (cx - 5, cy + 2)]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.line(pts + [pts[0]], fill=outline, width=2)


def draw_brain_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, fill, outline):
    draw.ellipse([cx - 22, cy - 16, cx + 2, cy + 16], fill=fill, outline=outline, width=2)
    draw.ellipse([cx - 2, cy - 16, cx + 22, cy + 16], fill=fill, outline=outline, width=2)
    draw.line([(cx, cy - 14), (cx, cy + 14)], fill=outline, width=2)
    draw.arc([cx - 15, cy - 8, cx - 3, cy + 6], 20, 210, fill=outline, width=2)
    draw.arc([cx + 3, cy - 8, cx + 15, cy + 6], 330, 160, fill=outline, width=2)


def draw_packet(draw: ImageDraw.ImageDraw, x: float, y: float, color):
    draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 255, 255), outline=color, width=3)
    draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=color)


def render_workflow_frame(fi: int, n_frames: int) -> Image.Image:
    W, H = 1440, 960
    t = fi / float(n_frames)
    img = Image.new("RGB", (W, H), (252, 251, 247))  # Warm paper canvas matching uploaded references
    draw = ImageDraw.Draw(img)

    # Subtle dot-paper texture
    for x in range(24, W, 32):
        for y in range(24, H, 32):
            draw.point((x, y), fill=(226, 224, 216))

    INK = (26, 32, 44)
    SUB_INK = (71, 85, 105)
    active_zone = int(t * 5) % 5

    # Title banner
    draw.text((28, 14), "CODEBASE AST, KNOWLEDGE GRAPH & DUAL VECTOR / VECTORLESS RAG ARCHITECTURE", fill=INK, font=F_H1)
    draw.text((28, 46), "Zero-dependency local indexing  |  11 Languages  |  Vectorless Graph + Dual Vector Embeddings + Hybrid RRF + KV-Cache / PagedAttention", fill=SUB_INK, font=F_BODY)
    draw.text((W - 230, 20), f"WORKFLOW FRAME {fi + 1:02d}/{n_frames}", fill=(147, 51, 234), font=F_MONO)

    # =====================================================================
    # ZONE 1 (TOP-LEFT YELLOW): INGESTION & AST EXTRACTION
    # =====================================================================
    z1 = (24, 74, 720, 244)
    draw_dashed_rounded_rect(draw, z1, 14, fill=(254, 243, 199), outline=(217, 119, 6), width=4 if active_zone == 0 else 2)
    draw.text((38, 82), "1. Ingestion, Delta Manifest & AST Extraction", fill=(180, 83, 9), font=F_ZONE)
    # 3 dense sub-columns separated by vertical dividers
    draw.line([(252, 108), (252, 234)], fill=(217, 119, 6), width=1)
    draw.line([(486, 108), (486, 234)], fill=(217, 119, 6), width=1)

    c1a = ["Repo & Incremental Delta", "- --repo URL | local path", "- git clone --depth 1", "- SHA-256 file_manifest.json", "- Delta: add/mod/unchg/del", "- --priority-paths (2.0x)", "- --exclude-dirs custom"]
    c1b = ["Multi-Lang AST Parser", "- Python stdlib ast.parse()", "- Java, TS/JS, Go, Rust, Kt,", "  C#, PHP structural parser", "- --chunk-strategy:", "  hybrid|function|class|file", "- #WHY/#NOTE/#ADR nodes"]
    c1c = ["Symbol & Type Metadata", "- Classes, Interfaces, Traits", "- Functions, Async, Methods", "- Exact start_line..end_line", "- Param & return annotations", "- Duplicate #L<line> IDs", "- Token est + sha256 hash"]
    for col_x, lines in [(38, c1a), (264, c1b), (498, c1c)]:
        draw.text((col_x, 110), lines[0], fill=INK, font=F_SUBH)
        for i, ln in enumerate(lines[1:]):
            draw.text((col_x, 130 + i * 17), ln, fill=SUB_INK, font=F_TINY)

    # =====================================================================
    # ZONE 2 (MID-LEFT ROSE/RED): LSP SYMBOL & KNOWLEDGE GRAPH ENGINE
    # =====================================================================
    z2 = (24, 260, 620, 444)
    draw_dashed_rounded_rect(draw, z2, 14, fill=(255, 228, 230), outline=(225, 29, 72), width=4 if active_zone == 1 else 2)
    draw.text((38, 268), "2. LSP Hierarchy & Confidence-Tagged Knowledge Graph", fill=(190, 18, 60), font=F_ZONE)
    draw.line([(322, 294), (322, 434)], fill=(225, 29, 72), width=1)

    c2a = ["Call, Type & Test Resolution", "- Same-lang-family call filter", "- Import-constrained binding", "- super_types & sub_types", "- super_implementations (overrides)", "- type_definitions & references", "- Direct + name-match test_map"]
    c2b = ["Graph Hygiene & Analytics", "- Edge tags: EXTRACTED | INFERRED", "  | AMBIGUOUS provenance", "- Production-isolated communities", "  (tests never hijack prod modules)", "- Builtin-filtered God Nodes", "- DFS Import Cycle detector"]
    for col_x, lines in [(38, c2a), (334, c2b)]:
        draw.text((col_x, 296), lines[0], fill=INK, font=F_SUBH)
        for i, ln in enumerate(lines[1:]):
            draw.text((col_x, 316 + i * 18), ln, fill=SUB_INK, font=F_TINY)

    # =====================================================================
    # ZONE 4 (TOP-RIGHT GREEN): 8-MODE RETRIEVAL & HYBRID RRF
    # =====================================================================
    z4 = (746, 74, 1416, 384)
    draw_dashed_rounded_rect(draw, z4, 14, fill=(220, 252, 231), outline=(22, 163, 74), width=4 if active_zone == 3 else 2)
    draw.text((762, 82), "4. 8-Mode Retrieval Engine & Hybrid Reciprocal Rank Fusion", fill=(21, 128, 61), font=F_ZONE)
    draw.line([(1086, 108), (1086, 234)], fill=(22, 163, 74), width=1)
    draw.line([(762, 240), (1400, 240)], fill=(22, 163, 74), width=1)

    c4a = ["Hybrid RRF & Vector Ranking", "- --mode hybrid: RRF(k=60)", "  1/(60+r_vec) + 1/(60+r_fts)", "  + 0.002 * ln(1 + graph_deg)", "- --mode vector: dual cosine", "  (0.6*nlp + 0.4*code) * boost", "- --mode fts: SQLite BM25*boost"]
    c4b = ["Graph & LSP Traversal Modes", "- --mode vectorless: PageIndex", "  tree + 1-hop graph subgraph", "- --mode explain: node degree,", "  community, rationale & edges", "- --mode path --target B: BFS", "  shortest path + weakest hop"]
    for col_x, lines in [(762, c4a), (1098, c4b)]:
        draw.text((col_x, 110), lines[0], fill=INK, font=F_SUBH)
        for i, ln in enumerate(lines[1:]):
            draw.text((col_x, 130 + i * 17), ln, fill=SUB_INK, font=F_TINY)

    # Bottom half of Green zone: Symbol Card + Interactive Explorer
    draw.text((762, 248), "IDE / LSP Symbol Card & Provenance Filtering", fill=INK, font=F_SUBH)
    c4c = [
        "- --mode symbol: returns definition (file:L1-L2), signature, callers, callees, super_types, sub_types, super_implementation, refs, tests",
        "- Priority-Path Boosting (--priority-paths): promotes core source packages (2.0x) above auxiliary scripts and fixtures",
        "- Token-First Budget: returns compact JSON/Markdown cards with exact line citations instead of dumping raw source files",
        "- Confidence Propagation: every edge & shortest-path hop explicitly exposes EXTRACTED vs INFERRED vs AMBIGUOUS",
    ]
    for i, ln in enumerate(c4c):
        draw.text((762, 268 + i * 22), ln, fill=SUB_INK, font=F_TINY)

    # =====================================================================
    # ZONE 3 (BOTTOM-LEFT BLUE): DUAL INDEXING LAYER (VECTORLESS + VECTOR)
    # =====================================================================
    z3 = (24, 694, 960, 938)
    draw_dashed_rounded_rect(draw, z3, 14, fill=(219, 234, 254), outline=(37, 99, 235), width=4 if active_zone == 2 else 2)
    draw.text((38, 702), "3. Dual Indexing Layer (--rag-mode both | vectorless | vector)", fill=(29, 78, 216), font=F_ZONE)
    for vx in (256, 488, 722):
        draw.line([(vx, 730), (vx, 926)], fill=(37, 99, 235), width=1)

    c3a = ["Vectorless Tree & Graph", "- tree_index.json (PageIndex)", "- graph.json (schema v3.0)", "- call_graph.json", "- type_hierarchy.json", "- references & test_map", "- 00-INDEX..05-GRAPH-REPORT", "- Interactive docs/graph.html"]
    c3b = ["Dual Chunk Representations", "- chunks.jsonl (AST chunks)", "- nlp_text: natural language", "  summary, doc, calls, notes", "- code_text: exact AST slice", "- camelCase/snake_case +", "  3-gram subword tokenizer", "- Zero text truncation loss"]
    c3c = ["Pluggable Embeddings", "- Default: offline tfidf", "  (D=128 L2-norm, 0 deps)", "- sentence-transformers", "  (all-MiniLM-L6-v2)", "- OpenAI text-embedding-3", "- Ollama nomic-embed-text", "- vectors.jsonl + meta.json"]
    c3d = ["Multi-Store Exports", "- rag_index.sqlite:", "  chunks_fts (FTS5 Porter)", "  + chunk_vectors (JSON)", "- qdrant_points.jsonl:", "  named nlp + code vectors", "- pgvector_schema.sql:", "  HALFVEC(dim) HNSW + GIN"]
    for col_x, lines in [(38, c3a), (268, c3b), (500, c3c), (734, c3d)]:
        draw.text((col_x, 732), lines[0], fill=INK, font=F_SUBH)
        for i, ln in enumerate(lines[1:]):
            draw.text((col_x, 754 + i * 21), ln, fill=SUB_INK, font=F_TINY)

    # =====================================================================
    # ZONE 5 (BOTTOM-RIGHT PURPLE): KV-CACHE & PAGED-ATTENTION PACKING
    # =====================================================================
    z5 = (982, 694, 1416, 938)
    draw_dashed_rounded_rect(draw, z5, 14, fill=(243, 232, 255), outline=(147, 51, 234), width=4 if active_zone == 4 else 2)
    draw.text((996, 702), "5. KV-Cache & PagedAttention", fill=(126, 34, 206), font=F_ZONE)

    c5 = [
        "Canonical Prefix Stability (--mode kv-pack)",
        "- Deterministic sort: (is_test, !priority, file, line)",
        "- Fixed 512-tok virtual pages (kv_paged_blocks.json)",
        "- Per-page SHA-256 prefix_hash + utilization %",
        "- Prompt framing for vLLM / SGLang / Prompt Cache:",
        "  <<<STATIC_KV_PREFIX_START>>>",
        "    # PagedAttention Block Table + AST Chunks",
        "  <<<STATIC_KV_PREFIX_END>>>",
        "  <<<DYNAMIC_QUERY_SUFFIX>>> User Query",
    ]
    draw.text((996, 732), c5[0], fill=INK, font=F_SUBH)
    for i, ln in enumerate(c5[1:]):
        col = (126, 34, 206) if "<<<" in ln else SUB_INK
        fnt = F_MONO if "<<<" in ln else F_TINY
        draw.text((996, 754 + i * 21), ln, fill=col, font=fnt)

    # =====================================================================
    # CENTRAL ANIMATED SPINE (Matching Uploaded Reference Flow!)
    # =====================================================================
    sy = 562
    # Dashed connectors from Zones into Spine (routed cleanly outside zone text)
    draw_dashed_line(draw, (650, 244), (650, 458), (217, 119, 6))
    draw_dashed_line(draw, (370, 444), (370, 540), (225, 29, 72))
    draw_dashed_line(draw, (650, 694), (650, 666), (37, 99, 235))
    draw_dashed_line(draw, (1030, 384), (1030, 540), (22, 163, 74))
    draw_dashed_line(draw, (1190, 694), (1190, 594), (147, 51, 234))

    # Spine nodes
    draw.rounded_rectangle([40, sy - 22, 185, sy + 22], radius=10, fill=(255, 255, 255), outline=INK, width=2)
    draw.text((54, sy - 10), "Repo / Query", fill=INK, font=F_SUBH)

    # Router circles (AST + Mode Router)
    r1 = (270, sy)
    r2 = (370, sy)
    r3 = (470, sy)
    draw_arrow(draw, (185, sy), (248, sy), INK, 3)
    draw.ellipse([r1[0] - 20, r1[1] - 20, r1[0] + 20, r1[1] + 20], fill=(254, 243, 199), outline=(217, 119, 6), width=3)
    draw.text((r1[0] - 13, r1[1] - 7), "AST", fill=INK, font=F_MONO)

    draw_arrow(draw, (290, sy), (348, sy), INK, 3)
    draw.ellipse([r2[0] - 20, r2[1] - 20, r2[0] + 20, r2[1] + 20], fill=(255, 228, 230), outline=(225, 29, 72), width=3)
    draw.text((r2[0] - 13, r2[1] - 7), "LSP", fill=INK, font=F_MONO)

    draw_arrow(draw, (390, sy), (448, sy), INK, 3)
    draw.ellipse([r3[0] - 20, r3[1] - 20, r3[0] + 20, r3[1] + 20], fill=(219, 234, 254), outline=(37, 99, 235), width=3)
    draw.text((r3[0] - 13, r3[1] - 7), "RAG", fill=INK, font=F_MONO)

    # Branch to 3 Stores: Graph DB (top), SQLite/pgvector (mid), Vector Store {} (bot)
    s_top = (650, 486)
    s_mid = (650, 562)
    s_bot = (650, 638)
    for tgt, col in [(s_top, (225, 29, 72)), (s_mid, (37, 99, 235)), (s_bot, (22, 163, 74))]:
        draw_arrow(draw, (490, sy), (tgt[0] - 32, tgt[1]), col, 3)

    draw_graph_icon(draw, s_top[0], s_top[1], 24, (255, 241, 242), (225, 29, 72))
    draw.text((s_top[0] + 32, s_top[1] - 12), "Graph DB", fill=INK, font=F_SUBH)
    draw.text((s_top[0] + 32, s_top[1] + 4), "graph.json", fill=SUB_INK, font=F_TINY)

    draw_cylinder_icon(draw, s_mid[0], s_mid[1], 46, 46, (239, 246, 255), (37, 99, 235), "FTS5")
    draw.text((s_mid[0] + 32, s_mid[1] - 12), "SQLite/pgvec", fill=INK, font=F_SUBH)
    draw.text((s_mid[0] + 32, s_mid[1] + 4), "BM25 + HNSW", fill=SUB_INK, font=F_TINY)

    draw_cylinder_icon(draw, s_bot[0], s_bot[1], 46, 46, (240, 253, 244), (22, 163, 74), "{ }")
    draw.text((s_bot[0] + 32, s_bot[1] - 12), "Vector Store", fill=INK, font=F_SUBH)
    draw.text((s_bot[0] + 32, s_bot[1] + 4), "Dual nlp+code", fill=SUB_INK, font=F_TINY)

    # Merge 3 stores -> Chunks -> RRF Funnel -> LLM Brain -> Answer
    chunks_pt = (895, sy)
    for src, col in [(s_top, (225, 29, 72)), (s_mid, (37, 99, 235)), (s_bot, (22, 163, 74))]:
        draw_arrow(draw, (src[0] + 132, src[1]), (chunks_pt[0] - 46, sy), col, 2)

    draw.rounded_rectangle([chunks_pt[0] - 44, sy - 26, chunks_pt[0] + 44, sy + 26], radius=8, fill=(255, 255, 255), outline=INK, width=2)
    draw.text((chunks_pt[0] - 32, sy - 14), "AST", fill=INK, font=F_SUBH)
    draw.text((chunks_pt[0] - 32, sy + 2), "Chunks", fill=SUB_INK, font=F_TINY)

    funnel_pt = (1030, sy)
    draw_arrow(draw, (chunks_pt[0] + 44, sy), (funnel_pt[0] - 22, sy), (22, 163, 74), 3)
    draw_funnel_icon(draw, funnel_pt[0], funnel_pt[1], (220, 252, 231), (22, 163, 74))
    draw.text((funnel_pt[0] - 34, sy + 22), "Hybrid RRF", fill=(21, 128, 61), font=F_MONO)

    brain_pt = (1190, sy)
    draw_arrow(draw, (funnel_pt[0] + 22, sy), (brain_pt[0] - 28, sy), (147, 51, 234), 3)
    draw_brain_icon(draw, brain_pt[0], brain_pt[1], (243, 232, 255), (147, 51, 234))
    draw.text((brain_pt[0] - 40, sy + 22), "KV-Packed LLM", fill=(126, 34, 206), font=F_MONO)

    ans_pt = (1355, sy)
    draw_arrow(draw, (brain_pt[0] + 28, sy), (ans_pt[0] - 46, sy), INK, 3)
    draw.rounded_rectangle([ans_pt[0] - 44, sy - 22, ans_pt[0] + 54, sy + 22], radius=10, fill=(220, 252, 231), outline=(22, 163, 74), width=2)
    draw.text((ans_pt[0] - 34, sy - 10), "Grounded", fill=(21, 128, 61), font=F_SUBH)

    # Animated packets flowing along the entire spine!
    if t < 0.25:
        u = ease(t / 0.25)
        draw_packet(draw, 185 + u * (470 - 185), sy, (217, 119, 6))
    elif t < 0.55:
        u = ease((t - 0.25) / 0.30)
        for tgt, col in [(s_top, (225, 29, 72)), (s_mid, (37, 99, 235)), (s_bot, (22, 163, 74))]:
            draw_packet(draw, 490 + u * (tgt[0] - 32 - 490), sy + u * (tgt[1] - sy), col)
    elif t < 0.80:
        u = ease((t - 0.55) / 0.25)
        draw_packet(draw, 880 + u * (1190 - 880), sy, (22, 163, 74))
    else:
        u = ease((t - 0.80) / 0.20)
        draw_packet(draw, 1190 + u * (1310 - 1190), sy, (147, 51, 234))

    return img


def render_setup_mp4_frame(fi: int, total_frames: int) -> Image.Image:
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (13, 17, 23))
    draw = ImageDraw.Draw(img)

    # Subtle grid
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=(20, 26, 36), width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=(20, 26, 36), width=1)

    t = fi / float(total_frames)
    step = min(3, int(t * 4))

    # Top header
    draw.rectangle([0, 0, W, 6], fill=(88, 166, 255))
    draw.text((40, 24), "codebase-ast-rag-indexer-skill  —  30-Second Setup & Walkthrough", fill=(240, 246, 252), font=F_TERM_H)
    draw.text((40, 56), "Zero external dependencies (Pure Python 3 stdlib)  |  Antigravity, Claude Code, Codex & Gemini CLI", fill=(139, 148, 158), font=F_BODY)

    # Step indicator pills
    steps = ["1. Clone Skill", "2. Index Repo (Dual RAG)", "3. Query (8 Modes)", "4. Explore Graph & Docs"]
    for i, st in enumerate(steps):
        px = 40 + i * 305
        act = (i == step)
        done = (i < step)
        bg = (22, 46, 78) if act else ((18, 44, 34) if done else (22, 27, 34))
        bd = (88, 166, 255) if act else ((63, 185, 80) if done else (48, 54, 61))
        tc = (240, 246, 252) if (act or done) else (139, 148, 158)
        draw.rounded_rectangle([px, 92, px + 288, 130], radius=8, fill=bg, outline=bd, width=2)
        draw.text((px + 14, 102), st, fill=tc, font=F_SUBH)

    # Terminal window
    tx0, ty0, tx1, ty1 = 40, 152, W - 40, H - 54
    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=12, fill=(10, 13, 18), outline=(48, 54, 61), width=2)
    draw.rectangle([tx0 + 2, ty0 + 2, tx1 - 2, ty0 + 36], fill=(22, 27, 34))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([tx0 + 16 + i * 20, ty0 + 12, tx0 + 28 + i * 20, ty0 + 24], fill=c)
    draw.text((tx0 + 84, ty0 + 11), "terminal — codebase-ast-rag-indexer-skill (v3.0)", fill=(139, 148, 158), font=F_MONO)

    step_scripts = [
        [
            ("$ git clone https://github.com/NallaSanjayReddy/codebase-ast-rag-indexer-skill.git", (88, 166, 255)),
            ("Cloning into 'codebase-ast-rag-indexer-skill'... done.", (139, 148, 158)),
            ("$ cd codebase-ast-rag-indexer-skill && python scripts/validate_manifests.py", (88, 166, 255)),
            ("OK: Validated 4 manifests (v3.0.0) and SKILL.md.", (63, 185, 80)),
            ("$ python -m unittest discover -s tests -v", (88, 166, 255)),
            ("test_dual_vector_and_vectorless_rag_pipeline ... ok", (63, 185, 80)),
            ("test_vectorless_only_mode ... ok   |   Ran 2 tests — OK", (63, 185, 80)),
            ("", (0, 0, 0)),
            ("# Ready for Antigravity, Claude Code, Codex & Gemini CLI (0 pip installs required!)", (251, 191, 36)),
        ],
        [
            ("$ python skills/codebase-ast-rag-indexer/scripts/ast_rag_indexer.py \\", (88, 166, 255)),
            ("    --repo https://github.com/pgvector/pgvector-python \\", (165, 214, 255)),
            ("    --output ./rag_out --rag-mode both --embedding-provider tfidf \\", (165, 214, 255)),
            ("    --page-size 512 --priority-paths pgvector --incremental", (165, 214, 255)),
            ("", (0, 0, 0)),
            ("Cloning https://github.com/pgvector/pgvector-python...", (139, 148, 158)),
            ("SUCCESS: Indexed 74 files -> 675 AST chunks, 675 dual vectors (tfidf d=128),", (63, 185, 80)),
            ("         2491 graph edges (15 production communities), 124 KV pages", (63, 185, 80)),
            ("Artifacts: chunks.jsonl | graph.json | vectors.jsonl | rag_index.sqlite | graph.html", (251, 191, 36)),
        ],
        [
            ("$ python query_rag.py --index ./rag_out/index --query 'async register vector' --mode hybrid", (88, 166, 255)),
            ("  #1 pgvector.psycopg.register.register_vector_async (rrf=0.0376 | vec=#2 | fts=#1)", (63, 185, 80)),
            ("", (0, 0, 0)),
            ("$ python query_rag.py --index ./rag_out/index --query Vector --target HalfVector --mode path", (88, 166, 255)),
            ("  Shortest path (2 hops) | Weakest-hop confidence: [EXTRACTED]", (251, 191, 36)),
            ("  Vector <--[calls|EXTRACTED]-- register_vector -->[calls|EXTRACTED]--> HalfVector", (210, 168, 255)),
            ("", (0, 0, 0)),
            ("$ python query_rag.py --index ./rag_out/index --query register_vector_async --mode kv-pack", (88, 166, 255)),
            ("  <<<STATIC_KV_PREFIX_START>>> [KV-Page 22 | sha256=8f14e45f] <<<DYNAMIC_QUERY_SUFFIX>>>", (45, 212, 191)),
        ],
        [
            ("$ ls ./rag_out/docs/", (88, 166, 255)),
            ("  00-INDEX.md                           # Executive metrics & RAG inventory", (240, 246, 252)),
            ("  01-TREE-INDEX-VECTORLESS-RAG.md       # PageIndex tree (no embeddings)", (240, 246, 252)),
            ("  02-CALL-AND-TYPE-HIERARCHY.md         # Callers, callees, super_implementations", (240, 246, 252)),
            ("  03-REFERENCES-AND-TESTS-MAP.md        # Cross-file refs + unit test map", (240, 246, 252)),
            ("  04-KV-CACHE-AND-PAGED-ATTENTION.md    # 512-tok virtual pages & prefix hashes", (240, 246, 252)),
            ("  05-GRAPH-REPORT.md                    # God Nodes, communities & import cycles", (240, 246, 252)),
            ("  graph.html                            # Interactive HTML5 force-directed graph", (63, 185, 80)),
            ("", (0, 0, 0)),
            ("All done! Open docs/graph.html in any browser or plug straight into your AI agent.", (251, 191, 36)),
        ],
    ]

    local_t = (t * 4) - step
    lines = step_scripts[step]
    n_show = max(1, int(min(1.0, local_t * 1.4) * len(lines)) + 1)
    for idx, (txt, col) in enumerate(lines[:n_show]):
        if txt:
            draw.text((tx0 + 24, ty0 + 56 + idx * 44), txt, fill=col, font=F_TERM_B if txt.startswith("$") else F_TERM)

    # Bottom progress bar
    bw = int((W - 80) * t)
    draw.rectangle([40, H - 30, W - 40, H - 22], fill=(22, 27, 34))
    draw.rectangle([40, H - 30, 40 + bw, H - 22], fill=(88, 166, 255))
    return img


def main():
    # 1. Render dense Excalidraw-style Workflow Overview GIF (1440x960)
    n_gif = 48
    gif_frames = [np.array(render_workflow_frame(i, n_gif)) for i in range(n_gif)]
    imageio.mimsave(OUT_GIF, gif_frames, duration=1.0 / 16.0, loop=0)
    print(f"SUCCESS: Rendered {OUT_GIF} ({OUT_GIF.stat().st_size // 1024} KB)")

    # 2. Render 24fps H.264 Setup Walkthrough MP4 (1280x720, 12 seconds = 288 frames)
    n_mp4 = 240
    writer = imageio.get_writer(OUT_MP4, fps=24, codec="libx264", pixelformat="yuv420p", macro_block_size=16)
    try:
        for i in range(n_mp4):
            writer.append_data(np.array(render_setup_mp4_frame(i, n_mp4)))
    finally:
        writer.close()
    print(f"SUCCESS: Rendered {OUT_MP4} ({OUT_MP4.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
