import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEXER = REPO_ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "ast_rag_indexer.py"
QUERY   = REPO_ROOT / "skills" / "codebase-ast-rag-indexer" / "scripts" / "query_rag.py"

SAMPLE_PY = """
class BaseStore:
    def search(self, query: str) -> list:
        return []

class PgVectorStore(BaseStore):
    def search(self, query: str) -> list:
        return self._execute_hnsw(query)

    def _execute_hnsw(self, query: str) -> list:
        return [query]
"""

SAMPLE_TEST_PY = """
from store import PgVectorStore

def test_pgvector_store_search():
    s = PgVectorStore()
    assert s.search("hello") == ["hello"]
"""

class TestCodebaseAstRagIndexer(unittest.TestCase):
    def test_full_ast_hierarchy_relations_and_kv_packing(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample_repo"
            (src / "tests").mkdir(parents=True)
            (src / "store.py").write_text(SAMPLE_PY, encoding="utf-8")
            (src / "tests" / "test_store.py").write_text(SAMPLE_TEST_PY, encoding="utf-8")

            out = Path(tmp) / "rag_out"
            subprocess.run([sys.executable, str(INDEXER), "--repo", str(src), "--output", str(out), "--page-size", "256"], check=True)

            # Verify Type Hierarchy & Super-Implementation resolution
            th = json.loads((out / "index" / "type_hierarchy.json").read_text(encoding="utf-8"))
            self.assertIn("store.PgVectorStore", th["types"])
            self.assertIn("store.BaseStore", th["types"]["store.PgVectorStore"]["super_types"])
            self.assertIn("store.PgVectorStore", th["types"]["store.BaseStore"]["sub_types"])
            self.assertEqual(th["super_implementations"].get("store.PgVectorStore.search"), "store.BaseStore.search")

            # Verify Call Hierarchy & Test Traceability
            cg = json.loads((out / "index" / "call_graph.json").read_text(encoding="utf-8"))
            self.assertIn("store.PgVectorStore._execute_hnsw", cg["outgoing"].get("store.PgVectorStore.search", []))
            tm = json.loads((out / "index" / "test_map.json").read_text(encoding="utf-8"))
            self.assertTrue(len(tm.get("store.PgVectorStore.search", [])) > 0)

            # Verify KV-Cache PagedAttention packing & query_rag.py modes
            kv = json.loads((out / "index" / "kv_paged_blocks.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(kv["total_pages"], 1)

            q_kv = subprocess.run([sys.executable, str(QUERY), "--index", str(out / "index"), "--query", "PgVectorStore search", "--mode", "kv-pack"], capture_output=True, text=True, check=True)
            self.assertIn("<<<STATIC_KV_PREFIX_START>>>", q_kv.stdout)
            self.assertIn("SuperImpl: store.BaseStore.search", q_kv.stdout)

            q_sym = subprocess.run([sys.executable, str(QUERY), "--index", str(out / "index"), "--query", "PgVectorStore", "--mode", "symbol"], capture_output=True, text=True, check=True)
            self.assertIn("store.BaseStore", q_sym.stdout)

if __name__ == "__main__":
    unittest.main()