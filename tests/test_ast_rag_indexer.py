import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEXER = ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "ast_rag_indexer.py"
QUERY = ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "query_rag.py"


class TestAstRagIndexerV3(unittest.TestCase):
    def _create_sample_repo(self, repo: Path):
        (repo / "core").mkdir(parents=True)
        (repo / "api").mkdir(parents=True)
        (repo / "web").mkdir(parents=True)
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
        # JS file with same function name 'score' to verify same-language-family isolation
        (repo / "web" / "client.js").write_text(
            "function score(x) { return x * 2; }\n",
            encoding="utf-8",
        )
        # Multiple tests calling HybridRetriever to verify production community isolation
        (repo / "tests" / "test_hybrid.py").write_text(
            "from core.hybrid import HybridRetriever\n\n"
            "def test_one():\n    return HybridRetriever().retrieve('a')\n"
            "def test_two():\n    return HybridRetriever().retrieve('b')\n"
            "def test_three():\n    return HybridRetriever().retrieve('c')\n"
            "def test_four():\n    return HybridRetriever().retrieve('d')\n",
            encoding="utf-8",
        )

    def test_dual_vector_and_vectorless_rag_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "sample_repo"
            out = Path(td) / "out"
            self._create_sample_repo(repo)

            res = subprocess.run(
                [
                    sys.executable, str(INDEXER),
                    "--repo", str(repo),
                    "--output", str(out),
                    "--rag-mode", "both",
                    "--embedding-provider", "tfidf",
                    "--embedding-dim", "64",
                    "--page-size", "256",
                    "--priority-paths", "core",
                    "--incremental",
                ],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("SUCCESS:", res.stdout)

            idx = out / "index"
            docs = out / "docs"

            for fname in [
                "chunks.jsonl", "tree_index.json", "graph.json", "call_graph.json",
                "type_hierarchy.json", "references.json", "test_map.json",
                "kv_paged_blocks.json", "rag_index.sqlite", "file_manifest.json",
                "pgvector_schema.sql", "vectors.jsonl", "vector_meta.json", "qdrant_points.jsonl",
            ]:
                self.assertTrue((idx / fname).exists(), f"Missing {fname}")

            # 1. Verify production community isolation (HybridRetriever must NOT be in 'tests' community)
            chunks = [json.loads(l) for l in (idx / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
            by_id = {c["chunk_id"]: c for c in chunks}
            self.assertNotEqual(by_id["core.hybrid.HybridRetriever"]["community_label"], "tests")
            self.assertEqual(by_id["tests.test_hybrid.test_one"]["community_label"], "tests")

            # 2. Verify same-language-family call isolation (Python retrieve must NOT call JS web.client.score)
            self.assertNotIn("web.client.score", by_id["core.hybrid.HybridRetriever.retrieve"]["callees"])
            self.assertIn("core.hybrid.HybridRetriever.score", by_id["core.hybrid.HybridRetriever.retrieve"]["callees"])

            # 3. Verify SQLite chunk_vectors table populated with dim=64
            conn = sqlite3.connect(str(idx / "rag_index.sqlite"))
            cnt = conn.execute("SELECT COUNT(*) FROM chunk_vectors WHERE dim = 64").fetchone()[0]
            conn.close()
            self.assertEqual(cnt, len(chunks))

            # 4. Verify --mode vector (pure vector cosine search)
            q_vec = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "BM25 dense cosine RRF", "--mode", "vector"],
                capture_output=True, text=True, check=True,
            )
            vec_res = json.loads(q_vec.stdout)["results"]
            self.assertGreater(len(vec_res), 0)
            self.assertIn("HybridRetriever", vec_res[0]["chunk_id"])

            # 5. Verify --mode hybrid (Reciprocal Rank Fusion)
            q_hyb = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "HybridRetriever retrieve", "--mode", "hybrid"],
                capture_output=True, text=True, check=True,
            )
            hyb_res = json.loads(q_hyb.stdout)["results"]
            self.assertGreater(len(hyb_res), 0)
            self.assertIsNotNone(hyb_res[0]["rrf_score"])

            # 6. Verify --mode vectorless (Tree + 1-hop Graph subgraph)
            q_vl = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "HybridRetriever", "--mode", "vectorless"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("Graph 1-hop:", q_vl.stdout)

            # 7. Verify --mode path & explain
            q_path = subprocess.run(
                [sys.executable, str(QUERY), "--index", str(idx), "--query", "handle_search", "--target", "BaseRetriever", "--mode", "path"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("Shortest path", q_path.stdout)

    def test_vectorless_only_mode(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "sample_repo"
            out = Path(td) / "out_vl"
            self._create_sample_repo(repo)
            subprocess.run(
                [sys.executable, str(INDEXER), "--repo", str(repo), "--output", str(out), "--rag-mode", "vectorless"],
                capture_output=True, text=True, check=True,
            )
            self.assertTrue((out / "index" / "graph.json").exists())
            self.assertFalse((out / "index" / "vectors.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
