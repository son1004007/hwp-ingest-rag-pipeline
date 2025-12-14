import os
import psycopg2
from sentence_transformers import SentenceTransformer

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASS", "postgres")
PG_TABLE = os.getenv("PG_TABLE", "doc_blocks")

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

_model = None
def _get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model

def get_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )

def retrieve_blocks_pgvector(question: str, top_k: int = 10):
    embedder = _get_embedder()
    q = embedder.encode([question], normalize_embeddings=True)[0]
    q_str = "[" + ",".join(f"{x:.6f}" for x in q.tolist()) + "]"

    # cosine distance: embedding <=> query_vec (낮을수록 유사)
    sql = f"""
    SELECT doc_id, block_id, block_type, content,
           (embedding <=> %s::vector) AS distance
    FROM public.{PG_TABLE}
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (q_str, q_str, top_k))
            rows = cur.fetchall()
        return [
            {"doc_id": r[0], "block_id": r[1], "block_type": r[2], "content": r[3], "distance": float(r[4])}
            for r in rows
        ]
    finally:
        conn.close()
