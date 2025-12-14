# scripts/embed_doc_blocks.py
import os
import time
import psycopg2
from psycopg2.extras import execute_values

from sentence_transformers import SentenceTransformer

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASS", "postgres")
PG_TABLE = os.getenv("PG_TABLE", "doc_blocks")

# 작은 다국어/한국어 대응 모델 (384 dim)
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

BATCH = int(os.getenv("EMBED_BATCH", "64"))
SLEEP = float(os.getenv("EMBED_SLEEP", "0"))  # 필요 시 부하 조절

def get_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )

def fetch_rows(conn, limit: int):
    sql = f"""
    SELECT id, content
    FROM public.{PG_TABLE}
    WHERE embedding IS NULL
      AND content IS NOT NULL
      AND length(content) > 0
    ORDER BY id
    LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        return cur.fetchall()

def update_embeddings(conn, id_vec_list):
    # vector는 pgvector가 text 배열 형태로 받습니다: '[0.1,0.2,...]'
    sql = f"""
    UPDATE public.{PG_TABLE} AS t
    SET embedding = v.embedding::vector,
        embedded_at = now()
    FROM (VALUES %s) AS v(id, embedding)
    WHERE t.id = v.id;
    """
    # (id, "[..]") 형태
    with conn.cursor() as cur:
        execute_values(cur, sql, id_vec_list, page_size=1000)

def main():
    print(f"[embed] model={EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    conn = get_conn()
    try:
        total = 0
        while True:
            rows = fetch_rows(conn, BATCH)
            if not rows:
                break

            ids = [r[0] for r in rows]
            texts = [r[1] for r in rows]

            vecs = model.encode(
                texts,
                batch_size=BATCH,
                show_progress_bar=False,
                normalize_embeddings=True,  # cosine 유리
            )

            payload = []
            for _id, v in zip(ids, vecs):
                v_str = "[" + ",".join(f"{x:.6f}" for x in v.tolist()) + "]"
                payload.append((_id, v_str))

            update_embeddings(conn, payload)
            conn.commit()

            total += len(rows)
            print(f"[embed] updated={len(rows)} total={total}")

            if SLEEP > 0:
                time.sleep(SLEEP)

        print(f"[embed] done. total_updated={total}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
