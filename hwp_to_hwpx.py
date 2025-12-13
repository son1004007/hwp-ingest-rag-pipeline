import os
from pyhwpx import Hwp

def convert_hwp_to_hwpx(hwp_path: str) -> str:
    hwp_path = os.path.abspath(hwp_path)
    base, ext = os.path.splitext(hwp_path)
    if ext.lower() != ".hwp":
        raise ValueError("입력 파일은 .hwp 여야 합니다.")

    hwpx_path = base + ".hwpx"

    hwp = Hwp()               # 내부적으로 COM 생성/보안처리 래핑
    hwp.open(hwp_path)        # 문서 열기
    hwp.save_as(hwpx_path)    # HWPX로 저장
    hwp.quit()

    return hwpx_path

if __name__ == "__main__":
    print(convert_hwp_to_hwpx(r"C:\temp\sample.hwp"))
