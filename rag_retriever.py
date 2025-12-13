# rag_retriever.py
import re
import psycopg2
import os

def extract_keywords_ko(question: str):
    """
    매우 단순한 한국어 키워드 추출 (RAG 최소 구현용)
    - 조사/어미 제거
    - 2글자 이상 토큰만 사용
    """
    tokens = re.split(r"[^\w가-힣]+", question)
    keywords = [t for t in tokens if len(t) >= 2]
    return list(dict.fromkeys(keywords))  # 중복 제거, 순서 유지

def get_conn_from_env():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DB", "postgres"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASS", "postgres"),
    )

def retrieve_blocks_fts(question: str, top_k: int = 12, table_name: str = "doc_blocks"):
    """
    PostgreSQL FTS(tsv) 기반으로 관련 블록을 top_k만큼 가져옵니다.
    """
    sql = f"""
    SELECT
        doc_id,
        block_id,
        block_type,
        content
    FROM public.{table_name}
    WHERE tsv @@ plainto_tsquery('simple', %s)
    ORDER BY id
    LIMIT %s;
    """

    conn = get_conn_from_env()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (question, top_k))
            rows = cur.fetchall()
        return [
            {
                "doc_id": r[0],
                "block_id": r[1],
                "block_type": r[2],
                "content": r[3],
            }
            for r in rows
        ]
    finally:
        conn.close()

def retrieve_blocks_fallback(question: str, top_k: int = 12, table_name: str = "doc_blocks"):
    keywords = extract_keywords_ko(question)
    if not keywords:
        return []

    where_clause = " OR ".join(["content ILIKE %s"] * len(keywords))
    sql = f"""
    SELECT doc_id, block_id, block_type, content
    FROM public.{table_name}
    WHERE {where_clause}
    ORDER BY id
    LIMIT %s;
    """

    params = [f"%{k}%" for k in keywords] + [top_k]

    conn = get_conn_from_env()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [
            {
                "doc_id": r[0],
                "block_id": r[1],
                "block_type": r[2],
                "content": r[3],
            }
            for r in rows
        ]
    finally:
        conn.close()

def format_context(blocks, max_chars: int = 12000) -> str:
    """
    LLM에 넣을 컨텍스트 문자열 생성(너무 길면 잘라냄).
    """
    parts = []
    total = 0
    for b in blocks:
        chunk = f"[doc_id={b['doc_id']} | block_id={b['block_id']} | type={b['block_type']}]\n{b['content']}\n"
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n---\n".join(parts)
