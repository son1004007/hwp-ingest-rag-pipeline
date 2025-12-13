# scripts/setup_hwp_registry.py
# -*- coding: utf-8 -*-
"""
한글(HWP) 자동화 시 '접근 허용' 보안 팝업을 줄이기 위한 레지스트리 등록 스크립트(1회 실행용)

- HKCU(현재 사용자) 아래에 모듈 등록:
  1) Software\HNC\HwpCtrl\Modules
  2) Software\HNC\HwpAutomation\Modules

- 값 이름: FilePathCheck (예제에서 자주 사용)
- 값 데이터: FilePathCheckerModule.dll의 전체 경로

사용:
  python scripts/setup_hwp_registry.py "C:\\Users\\son10\\venv\\Lib\\site-packages\\pyhwpx\\FilePathCheckerModule.dll"

확인:
  regedit 실행 → 위 경로에 값이 생성됐는지 확인
"""

import os
import sys
import winreg


DEFAULT_VALUE_NAME = "FilePathCheck"
TARGET_SUBKEYS = [
    r"Software\HNC\HwpCtrl\Modules",
    r"Software\HNC\HwpAutomation\Modules",
]


def set_reg_sz(root, subkey: str, name: str, data: str) -> None:
    key = winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, data)
    finally:
        winreg.CloseKey(key)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/setup_hwp_registry.py <full_path_to_FilePathCheckerModule.dll>")
        sys.exit(1)

    dll_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"DLL not found: {dll_path}")

    for subkey in TARGET_SUBKEYS:
        set_reg_sz(winreg.HKEY_CURRENT_USER, subkey, DEFAULT_VALUE_NAME, dll_path)
        print(f"[OK] HKCU\\{subkey} : {DEFAULT_VALUE_NAME} = {dll_path}")

    print("\nDone. 한글(HWP) 프로세스를 완전히 종료 후 다시 실행해서 효과를 확인하세요.")


if __name__ == "__main__":
    main()
# 실행 예시
# python scripts\setup_hwp_registry.py "C:\Users\son10\venv\Lib\site-packages\pyhwpx\FilePathCheckerModule.dll"
