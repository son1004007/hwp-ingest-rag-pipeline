-- HNSW 인덱스 (지원되는 경우)
CREATE INDEX IF NOT EXISTS ix_doc_blocks_embedding_hnsw
ON public.doc_blocks
USING hnsw (embedding vector_cosine_ops);
