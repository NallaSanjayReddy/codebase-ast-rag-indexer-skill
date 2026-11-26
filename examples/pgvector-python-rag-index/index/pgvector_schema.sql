-- PostgreSQL pgvector 0.8+ Hybrid AST RAG Schema (HNSW halfvec + GIN tsvector)
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
