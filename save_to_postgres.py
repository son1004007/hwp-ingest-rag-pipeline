# save_to_postgres.py
import psycopg2
from psycopg2.extras import Json

from hwp_ingest_pipeline import hwp_to_langchain_docs

HWP_PATH = r"C:\Users\son10\Documents\HWP paser\3_ [첨부] 개인정보 수집이용 및 제3자 제공동의서.hwp"

# ✅ 로컬 기본 설치 가정
PG_HOST = "localhost"
PG_PORT = 5432
PG_DB   = "postgres"   # 필요하면 변경
PG_USER = "postgres"   # 기본계정 사용 가정
PG_PASS = "postgres"   # 비밀번호=계정이라고 하셨으니 기본값

TABLE_NAME = "doc_blocks"


def get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )


def ensure_table(conn):
    """
    doc_blocks 테이블이 없으면 생성하고,
    재적재/중복 방지용 unique index까지 생성합니다.
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id            BIGSERIAL PRIMARY KEY,
        doc_id        TEXT,
        doc_title     TEXT,
        section_title TEXT,
        section_path  TEXT,
        block_id      TEXT,
        block_type    TEXT,
        content       TEXT NOT NULL,
        metadata      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    -- 같은 문서/같은 블록은 중복 저장하지 않기(업서트용)
    CREATE UNIQUE INDEX IF NOT EXISTS ux_{TABLE_NAME}_docid_blockid
    ON {TABLE_NAME} (doc_id, block_id);

    CREATE INDEX IF NOT EXISTS ix_{TABLE_NAME}_docid
    ON {TABLE_NAME} (doc_id);

    CREATE INDEX IF NOT EXISTS ix_{TABLE_NAME}_blocktype
    ON {TABLE_NAME} (block_type);
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def save_documents(conn, docs):
    sql = f"""
    INSERT INTO {TABLE_NAME}
    (doc_id, doc_title, section_title, section_path, block_id, block_type, content, metadata)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (doc_id, block_id) DO UPDATE
    SET
      doc_title     = EXCLUDED.doc_title,
      section_title = EXCLUDED.section_title,
      section_path  = EXCLUDED.section_path,
      block_type    = EXCLUDED.block_type,
      content       = EXCLUDED.content,
      metadata      = EXCLUDED.metadata
    ;
    """

    rows = []
    for d in docs:
        m = d.metadata or {}
        rows.append((
            m.get("doc_id"),
            m.get("doc_title"),
            m.get("section_title"),
            m.get("section_path"),
            m.get("block_id"),
            m.get("block_type"),
            d.page_content,
            Json(m),   # metadata를 jsonb로 저장
        ))

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

    conn.commit()
    return len(rows)


def print_summary(conn, doc_id: str):
    """
    적재 후 기본 확인용 요약 출력
    """
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT block_type, COUNT(*)
            FROM {TABLE_NAME}
            WHERE doc_id = %s
            GROUP BY block_type
            ORDER BY block_type;
        """, (doc_id,))
        by_type = cur.fetchall()

        cur.execute(f"""
            SELECT block_id, block_type, LEFT(content, 120) AS preview
            FROM {TABLE_NAME}
            WHERE doc_id = %s
            ORDER BY id
            LIMIT 5;
        """, (doc_id,))
        samples = cur.fetchall()

    print("\n[DB 적재 요약]")
    print(" - 전체 row 수:", total)
    print(" - 현재 문서 block_type별:", by_type)
    print(" - 샘플 5개:")
    for r in samples:
        print("   ", r)



if __name__ == "__main__":
    docs = hwp_to_langchain_docs(HWP_PATH)
    print("생성된 Document:", len(docs))

    if not docs:
        print("Document가 0개라서 DB 저장을 중단합니다. (파싱 결과 확인 필요)")

    doc_id = docs[0].metadata.get("doc_id")

    conn = get_conn()
    try:
        ensure_table(conn)
        n = save_documents(conn, docs)
        print("PostgreSQL 저장 완료. upsert rows:", n)
        print_summary(conn, doc_id)
    finally:
        conn.close()

