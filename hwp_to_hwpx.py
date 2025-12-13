# hwp_to_hwpx.py
import os
import win32com.client as win32

def convert_hwp_to_hwpx(hwp_path: str) -> str:
    """
    주어진 .hwp 파일을 한글 자동화로 열어서 .hwpx로 저장한 뒤, 저장된 경로를 반환.
    """
    hwp_path = os.path.abspath(hwp_path)
    base, ext = os.path.splitext(hwp_path)

    if ext.lower() != ".hwp":
        raise ValueError("입력 파일은 .hwp 여야 합니다.")

    hwpx_path = base + ".hwpx"

    # 한글 실행 (HWPFrame.HwpObject)
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    # 보안 경고창 방지 (파일 경로 체크 모듈 비활성화)
    # 한컴 문서 예제에서 많이 쓰는 패턴
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        # 버전에 따라 없을 수도 있으니 실패해도 진행
        pass

    # (1) 메시지 박스 자동 처리 (팝업 자동 클릭)
    # 값은 환경/팝업 종류에 따라 달라질 수 있는데,
    # 우선 범용으로 많이 쓰이는 값부터 시도합니다.
    try:
        hwp.SetMessageBoxMode(0x00211411)
    except Exception:
        pass

    # (2) Open 시 버전 경고 끄기
    # forum에서 Open args로 versionwarning:false 지원 언급
    # 옵션 구분자는 환경에 따라 ';' 또는 ','로 들어가기도 해서 ';'로 시작
    open_args = "forceopen:true;versionwarning:false"


    # 문서 열기
    # "HWP" 포맷 + forceopen 옵션
    hwp.Open(hwp_path, "HWP", "forceopen:true")

    # HWPX로 저장 (공식 문서 기준 format="HWPX")
    # https://developer.hancom.com/webhwp/devguide/hwpctrl/methods/saveas
    ok = hwp.SaveAs(hwpx_path, "HWPX", "")

    # 한글 종료
    hwp.Quit()

    if not ok:
        raise RuntimeError("HWP → HWPX 변환 실패")

    return hwpx_path

if __name__ == "__main__":
    hwpx = convert_hwp_to_hwpx(r"C:\temp\sample.hwp")
    print("변환 완료:", hwpx)
