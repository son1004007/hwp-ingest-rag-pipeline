# json_to_langchain_docs.py
from typing import List
try:
    # 최신 권장 경로 (langchain-core)
    from langchain_core.documents import Document
except Exception:
    # 구버전 호환
    from langchain.docstore.document import Document
    
def json_to_documents(json_doc: dict) -> List[Document]:
    docs: List[Document] = []

    for section in json_doc.get("sections", []):
        section_title = section.get("title", "")
        section_path = section.get("path", "")

        for block in section.get("content_blocks", []):
            block_type = block.get("type")

            if block_type == "paragraph":
                content = block.get("text", "")

            elif block_type == "table":
                headers = block.get("headers", [])
                rows = block.get("rows", [])
                caption = block.get("caption", "")

                # Markdown 테이블로 직렬화
                if headers:
                    header_line = "| " + " | ".join(headers) + " |"
                    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                    row_lines = [
                        "| " + " | ".join(row) + " |"
                        for row in rows
                    ]
                    table_md = "\n".join([header_line, sep_line] + row_lines)
                else:
                    table_md = "\n".join(
                        "| " + " | ".join(row) + " |" for row in rows
                    )

                content = f"[{caption}]\n{table_md}".strip()

            else:
                # 기타 타입은 일단 무시
                continue

            if not content:
                continue

            metadata = {
                "doc_id": json_doc.get("doc_id"),
                "doc_title": json_doc.get("title"),
                "section_title": section_title,
                "section_path": section_path,
                "block_id": block.get("block_id"),
                "block_type": block_type,
            }

            docs.append(Document(page_content=content, metadata=metadata))

    return docs

if __name__ == "__main__":
    from hwpx_to_json import hwpx_to_json

    json_doc = hwpx_to_json(r"C:\temp\sample.hwpx")
    docs = json_to_documents(json_doc)
    print("생성된 Document 개수:", len(docs))
    print("예시 1개:\n", docs[0].page_content)
    print("metadata:", docs[0].metadata)
