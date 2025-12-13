# save_to_postgres.py
import os
import glob
import psycopg2
from psycopg2.extras import Json

from hwp_ingest_pipeline import hwp_to_langchain_docs

# ✅ HWP 폴더 경로 (여기만 바꾸면 됨)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HWP_DIR = os.path.join(BASE_DIR, "hwp_doc")

# ✅ 로컬 기본 설치 가정
PG_HOST = "localhost"
PG_PORT = 5432
PG_DB   = "postgres"
PG_USER = "postgres"
PG_PASS = "postgres"

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
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NULL
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
    """
    (doc_id, block_id) 충돌 시 UPDATE + updated_at 갱신
    """
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
      metadata      = EXCLUDED.metadata,
      updated_at    = now()
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
            Json(m),
        ))

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

    conn.commit()
    return len(rows)


def list_hwp_files(root_dir: str):
    root_dir = os.path.abspath(root_dir)
    patterns = [
        os.path.join(root_dir, "*.hwp"),
        os.path.join(root_dir, "*.HWP"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    # 파일명 기준 정렬(재현성)
    files = sorted(set(files))
    return files


def print_doc_summary(conn, doc_id: str):
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT block_type, COUNT(*)
            FROM {TABLE_NAME}
            WHERE doc_id = %s
            GROUP BY block_type
            ORDER BY block_type;
        """, (doc_id,))
        by_type = cur.fetchall()
    print(f"  - block_type별: {by_type}")


def main():
    files = list_hwp_files(HWP_DIR)
    if not files:
        print("적재할 .hwp 파일이 없습니다:", HWP_DIR)
        return

    conn = get_conn()
    try:
        ensure_table(conn)

        total_docs = 0
        total_rows = 0
        ok = 0
        fail = 0

        for i, path in enumerate(files, start=1):
            print(f"\n[{i}/{len(files)}] 처리 시작: {os.path.basename(path)}")
            try:
                docs = hwp_to_langchain_docs(path)
                print("  생성된 Document:", len(docs))
                if not docs:
                    print("  Document가 0개라서 스킵합니다.")
                    continue

                doc_id = (docs[0].metadata or {}).get("doc_id") or os.path.splitext(os.path.basename(path))[0]

                n = save_documents(conn, docs)
                total_docs += 1
                total_rows += n
                ok += 1

                print(f"  PostgreSQL 저장 완료. upsert rows: {n}")
                print_doc_summary(conn, doc_id)

            except Exception as e:
                fail += 1
                print("  [FAIL]", type(e).__name__, str(e))

        print("\n[배치 적재 완료]")
        print(" - 처리 파일 수:", len(files))
        print(" - 성공:", ok)
        print(" - 실패:", fail)
        print(" - 적재 문서 수(성공 기준):", total_docs)
        print(" - upsert rows 합계:", total_rows)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
