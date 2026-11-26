import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEXER = ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "ast_rag_indexer.py"
QUERY = ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "query_rag.py"


class TestAstRagIndexerV2(unittest.TestCase):
    def _create_sample_repo(self, repo: Path):
        (repo / "core").mkdir(parents=True)
        (repo / "api").mkdir(parents=True)
        (repo / "tests").mkdir(parents=True)

        (repo / "core" / "base.py").write_text(
            "# WHY: BaseRetriever enforces deterministic pagination for KV-cache reuse\n"
            "class BaseRetriever:\n"
            "    def retrieve(self, query: str) -> list:\n"
            "        return []\n",
            encoding="utf-8",
        )
        (repo / "core" / "hybrid.py").write_text(
            "from core.base import BaseRetriever\n\n"
            "class HybridRetriever(BaseRetriever):\n"
            "    # NOTE: Merges BM25 and dense cosine scores via RRF\n"
            "    def retrieve(self, query: str) -> list:\n"
            "        return self.score(query)\n\n"
            "    def score(self, query: str) -> list:\n"
            "        return [query]\n",
            encoding="utf-8",
        )
        (repo / "api" / "handler.py").write_text(
            "from core.hybrid import HybridRetriever\n\n"
            "def handle_search(retriever: HybridRetriever, q: str) -> list:\n"
            "    return retriever.retrieve(q)\n",
            encoding="utf-8",
        )
        (repo / "tests" / "test_hybrid.py").write_text(
            "from core.hybrid import HybridRetriever\n\n"
            "def test_hybrid_retrieve():\n"
            "    r = HybridRetriever()\n"
            "    assert r.retrieve('hello') == ['hello']\n",
            encoding="utf-8",
        )

    def test_full_v2_pipeline_and_all_query_modes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "sample_repo"
            out = Path(td) / "out"
            self._create_sample_repo(repo)

            res = subprocess.run(
                [
                    sys.executable, str(INDEXER),
                    "--repo", str(repo),
                    "--output", str(out),
                    "--page-size", "256",
                    "--chunk-strategy", "hybrid",
                    "--priority-paths", "core",
                    "--incremental",
                ],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("SUCCESS:", res.stdout)

            idx = out / "index"
            docs = out / "docs"

            # Verify core v1 + v2 artifacts exist
            for fname in [
                "chunks.jsonl", "tree_index.json", "graph.json", "call_graph.json",
                "type_hierarchy.json", "references.json", "test_map.json",
                "kv_paged_blocks.json", "rag_index.sqlite", "file_manifest.json", "pgvector_schema.sql",
            ]:
                self.assertTrue((idx / fname).exists(), f"Missing {fname}")

            for dname in [
                "00-INDEX.md", "01-TREE-INDEX-VECTORLESS-RAG.md", "02-CALL-AND-TYPE-HIERARCHY.md",
                "03-REFERENCES-AND-TESTS-MAP.md", "04-KV-CACHE-AND-PAGED-ATTENTION-PACKING.md",
                "05-GRAPH-REPORT.md", "graph.html",
            ]:
                self.assertTrue((docs / dname).exists(), f"Missing {dname}")

            # Verify type hierarchy, super_implementation, dual nlp_text/code_text, priority_boost, rationale
            th = json.loads((idx / "type_hierarchy.json").read_text(encoding="utf-8"))
            self.assertIn("core.hybrid.HybridRetriever.retrieve", th["super_implementations"])
            self.assertEqual(
                th["super_implementations"]["core.hybrid.HybridRetriever.retrieve"],
                "core.base.BaseRetriever.retrieve",
            )

            chunks = [json.loads(line) for line in (idx / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            by_id = {c["chunk_id"]: c for c in chunks}
            self.assertEqual(by_id["core.hybrid.HybridRetriever"]["priority_boost"], 2.0)
            self.assertEqual(by_id["api.handler.handle_search"]["priority_boost"], 1.0)
            self.assertIn("HybridRetriever", by_id["core.hybrid.HybridRetriever"]["nlp_text"])
            self.assertTrue(len(by_id["core.base.BaseRetriever"]["rationale"]) >= 1)

            # Verify Graphify-style graph.json (confidence tags, god_nodes, communities)
            graph = json.loads((idx / "graph.json").read_text(encoding="utf-8"))
            self.assertGreater(graph["stats"]["edges"], 0)
            self.assertTrue(all(e["confidence"] in ("EXTRACTED", "INFERRED", "AMBIGUOUS") for e in graph["edges"]))
            self.assertGreater(len(graph["god_nodes"]), 0)

            # Test all 6 query modes
            q_explain = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "HybridRetriever", "--mode", "explain"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("Node: core.hybrid.HybridRetriever", q_explain.stdout)
            self.assertIn("Community:", q_explain.stdout)

            q_path = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "handle_search", "--target", "BaseRetriever", "--mode", "path"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("Shortest path", q_path.stdout)
            self.assertIn("Overall confidence", q_path.stdout)

            q_fts = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "BM25 RRF retrieve", "--mode", "fts"],
                capture_output=True, text=True, check=True,
            )
            fts_payload = json.loads(q_fts.stdout)
            self.assertGreater(len(fts_payload["results"]), 0)

            q_kv = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "HybridRetriever", "--mode", "kv-pack"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("<<<STATIC_KV_PREFIX_START>>>", q_kv.stdout)
            self.assertIn("<<<DYNAMIC_QUERY_SUFFIX>>>", q_kv.stdout)

            # Test incremental re-run delta (0 added, 0 modified, 4 unchanged)
            res2 = subprocess.run(
                [sys.executable, str(INDEXER), "--repo", str(repo), "--output", str(out), "--incremental"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("SUCCESS:", res2.stdout)
            report = (docs / "05-GRAPH-REPORT.md").read_text(encoding="utf-8")
            self.assertIn("Unchanged: `4`", report)

    def test_chunk_strategy_file_and_class(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "sample_repo"
            out_cls = Path(td) / "out_cls"
            out_file = Path(td) / "out_file"
            self._create_sample_repo(repo)

            subprocess.run(
                [sys.executable, str(INDEXER), "--repo", str(repo), "--output", str(out_cls), "--chunk-strategy", "class"],
                capture_output=True, text=True, check=True,
            )
            cls_chunks = [json.loads(l) for l in (out_cls / "index" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertTrue(all(c["kind"] == "class" for c in cls_chunks))

            subprocess.run(
                [sys.executable, str(INDEXER), "--repo", str(repo), "--output", str(out_file), "--chunk-strategy", "file"],
                capture_output=True, text=True, check=True,
            )
            file_chunks = [json.loads(l) for l in (out_file / "index" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertEqual(len(file_chunks), 4)
            self.assertTrue(all(c["kind"] == "file" for c in file_chunks))


if __name__ == "__main__":
    unittest.main()
