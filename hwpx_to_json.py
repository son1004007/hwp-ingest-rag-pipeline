# hwpx_to_json.py
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List


def _is_text_tag(tag: str) -> bool:
    # 네임스페이스를 포함한 태그에서 로컬명을 대충 판별
    # 예: {ns}t , {ns}text 등이 흔함
    local = tag.split("}")[-1].lower()
    return local in ("t", "text", "char", "run")  # run/char도 텍스트가 들어오는 문서가 있어 포함


def extract_text_from_p(p_elem: ET.Element) -> str:
    # HWPX는 텍스트가 다양한 하위 태그에 들어갈 수 있어
    # 네임스페이스 무시 + 텍스트 노드 중심으로 최대한 수집
    texts: List[str] = []
    for el in p_elem.iter():
        if el.text and el.text.strip():
            # 텍스트 태그일 가능성이 높은 경우 우선 수집
            if _is_text_tag(el.tag) or el.tag.split("}")[-1].lower() in ("t", "text"):
                texts.append(el.text.strip())
            else:
                # 그 외 태그의 text도 경우에 따라 실제 문장인 경우가 있어 포함
                texts.append(el.text.strip())
        if el.tail and el.tail.strip():
            texts.append(el.tail.strip())
    # 중복 공백 정리
    out = " ".join(texts).strip()
    out = " ".join(out.split())
    return out


def extract_table(tbl_elem: ET.Element) -> Dict[str, Any]:
    rows: List[List[str]] = []

    for tr in tbl_elem.findall(".//{*}tr"):
        row_texts: List[str] = []
        for tc in tr.findall(".//{*}tc"):
            cell_texts: List[str] = []
            for p in tc.findall(".//{*}p"):
                txt = extract_text_from_p(p)
                if txt:
                    cell_texts.append(txt)
            row_texts.append(" / ".join(cell_texts).strip())
        if any(c for c in row_texts):
            rows.append(row_texts)

    if not rows:
        return {"headers": [], "rows": []}

    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    return {"headers": headers, "rows": data_rows}


def hwpx_to_json(hwpx_path: str) -> Dict[str, Any]:
    hwpx_path = os.path.abspath(hwpx_path)

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        names = zf.namelist()

        # ✅ section0.xml 고정이 아니라 section*.xml 자동 탐색
        section_files = sorted(
            [n for n in names if n.lower().startswith("contents/section") and n.lower().endswith(".xml")]
        )
        if not section_files:
            raise FileNotFoundError("HWPX 내부에서 Contents/section*.xml 을 찾지 못했습니다.")

        sections = []
        sec_idx = 0

        for sfile in section_files:
            with zf.open(sfile) as f:
                tree = ET.parse(f)
                root = tree.getroot()

            content_blocks = []
            block_idx = 0

            # ✅ 문단 수집: 표 안의 p까지 함께 잡힐 수 있어서,
            #    우선 전체 p를 수집하되, 너무 많으면 나중에 개선(필터링)하면 됩니다.
            ps = root.findall(".//{*}p")
            for p in ps:
                text = extract_text_from_p(p)
                if text:
                    block_idx += 1
                    content_blocks.append(
                        {"block_id": f"sec{sec_idx}-p{block_idx}", "type": "paragraph", "text": text}
                    )

            # ✅ 표 수집
            tbls = root.findall(".//{*}tbl")
            t_idx = 0
            for tbl in tbls:
                t_idx += 1
                table_data = extract_table(tbl)
                block_idx += 1
                content_blocks.append(
                    {
                        "block_id": f"sec{sec_idx}-tbl{t_idx}",
                        "type": "table",
                        "caption": f"{os.path.basename(sfile)} 표 {t_idx}",
                        "headers": table_data["headers"],
                        "rows": table_data["rows"],
                    }
                )

            sections.append(
                {
                    "id": str(sec_idx),
                    "title": os.path.basename(sfile),
                    "path": f"{sec_idx+1}",
                    "content_blocks": content_blocks,
                }
            )
            sec_idx += 1

    doc_json: Dict[str, Any] = {
        "doc_id": os.path.splitext(os.path.basename(hwpx_path))[0],
        "title": os.path.basename(hwpx_path),
        "meta": {"source_path": hwpx_path, "format": "hwpx"},
        "sections": sections,
    }
    return doc_json


if __name__ == "__main__":
    doc = hwpx_to_json(r"C:\temp\sample.hwpx")
    # 간단 검증
    total_blocks = sum(len(s["content_blocks"]) for s in doc["sections"])
    print("sections:", len(doc["sections"]), "total_blocks:", total_blocks)
