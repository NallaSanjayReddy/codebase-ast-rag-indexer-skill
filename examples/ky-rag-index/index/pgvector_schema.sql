-- PostgreSQL pgvector 0.8+ Dual-Embedding Hybrid AST RAG Schema (dim=128)
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
    nlp_embedding HALFVEC(128),
    code_embedding HALFVEC(128)
);

CREATE INDEX IF NOT EXISTS idx_ast_chunks_nlp_hnsw  ON code_ast_chunks USING hnsw (nlp_embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_code_hnsw ON code_ast_chunks USING hnsw (code_embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_fts       ON code_ast_chunks USING gin (fts);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_page      ON code_ast_chunks (repo_name, kv_page_id);
CREATE INDEX IF NOT EXISTS idx_ast_chunks_comm      ON code_ast_chunks (repo_name, community_id);
