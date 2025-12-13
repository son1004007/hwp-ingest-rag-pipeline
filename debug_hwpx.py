# debug_hwpx.py
import zipfile
import xml.etree.ElementTree as ET

def debug_hwpx(hwpx_path: str):
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        names = zf.namelist()
        print("[ZIP entries sample]")
        for n in names[:30]:
            print(" -", n)

        section_files = [n for n in names if n.lower().startswith("contents/section") and n.lower().endswith(".xml")]
        print("\n[section xml files]")
        for s in section_files:
            print(" -", s)

        if not section_files:
            print("\nsection*.xml 을 찾지 못했습니다.")
            return

        # 첫 section 하나만 열어서 p/tbl 개수 확인
        s0 = section_files[0]
        with zf.open(s0) as f:
            tree = ET.parse(f)
            root = tree.getroot()
        ps = root.findall(".//{*}p")
        tbls = root.findall(".//{*}tbl")
        print(f"\n[{s0}] root tag =", root.tag)
        print("p count =", len(ps))
        print("tbl count =", len(tbls))

if __name__ == "__main__":
    debug_hwpx(r"C:\Users\son10\Documents\HWP paser\3_ [첨부] 개인정보 수집이용 및 제3자 제공동의서.hwpx")
