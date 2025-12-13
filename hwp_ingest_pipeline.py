# hwp_ingest_pipeline.py
from hwp_to_hwpx import convert_hwp_to_hwpx
from hwpx_to_json import hwpx_to_json
from json_to_langchain_docs import json_to_documents

def hwp_to_langchain_docs(hwp_path: str):
    # 1) HWP → HWPX
    hwpx_path = convert_hwp_to_hwpx(hwp_path)

    # 2) HWPX(XML) → JSON 구조
    json_doc = hwpx_to_json(hwpx_path)

    # 3) JSON → LangChain Document 리스트
    docs = json_to_documents(json_doc)
    return docs

if __name__ == "__main__":
    docs = hwp_to_langchain_docs(r"./3_ [첨부] 개인정보 수집이용 및 제3자 제공동의서.hwp")
    print("Document 개수:", len(docs))
    for i, d in enumerate(docs[:3], start=1):
        print(f"\n=== DOC {i} ===")
        print(d.page_content[:500], "...")
        print("metadata:", d.metadata)
