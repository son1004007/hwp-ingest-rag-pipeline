import os
import time
import threading
import win32com.client as win32
import win32gui
import win32con
import win32process
import ctypes

user32 = ctypes.windll.user32

# -------------------------------
# SendInput 기반 Shift+Y
# -------------------------------
def send_shift_y():
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong),
                    ("ki", KEYBDINPUT)]

    def key(vk, up=False):
        return INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=vk,
                wScan=0,
                dwFlags=KEYEVENTF_KEYUP if up else 0,
                time=0,
                dwExtraInfo=None
            )
        )

    inputs = (INPUT * 4)(
        key(win32con.VK_SHIFT),
        key(ord('Y')),
        key(ord('Y'), up=True),
        key(win32con.VK_SHIFT, up=True),
    )

    user32.SendInput(4, ctypes.byref(inputs), ctypes.sizeof(INPUT))

# -------------------------------
# HWP 팝업 감시자
# -------------------------------
def popup_watcher(stop_event, hwp_pid):
    while not stop_event.is_set():

        def enum_cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            cls = win32gui.GetClassName(hwnd)
            if cls != "#32770":
                return

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid != hwp_pid:
                return

            # 팝업 발견 → 강제 전면 + 입력
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                send_shift_y()
            except Exception:
                pass

        win32gui.EnumWindows(enum_cb, None)
        time.sleep(0.2)

# -------------------------------
# 변환 함수
# -------------------------------
def convert_hwp_to_hwpx(hwp_path: str) -> str:
    hwp_path = os.path.abspath(hwp_path)
    base, ext = os.path.splitext(hwp_path)
    if ext.lower() != ".hwp":
        raise ValueError("입력 파일은 .hwp 여야 합니다.")

    hwpx_path = base + ".hwpx"

    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    # HWP PID 확보
    hwp_hwnd = hwp.XHwpWindows.Item(0).Handle
    _, hwp_pid = win32process.GetWindowThreadProcessId(hwp_hwnd)

    stop_event = threading.Event()
    watcher = threading.Thread(
        target=popup_watcher,
        args=(stop_event, hwp_pid),
        daemon=True
    )
    watcher.start()

    try:
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        except Exception:
            pass

        try:
            hwp.SetMessageBoxMode(0x111111)
        except Exception:
            pass

        open_args = "forceopen:true;versionwarning:false"
        hwp.Open(hwp_path, "HWP", open_args)

        ok = hwp.SaveAs(hwpx_path, "HWPX", "")
        if not ok:
            raise RuntimeError("HWP → HWPX 변환 실패")

    finally:
        try:
            hwp.Quit()
        except Exception:
            pass
        stop_event.set()

    return hwpx_path


if __name__ == "__main__":
    print(convert_hwp_to_hwpx(r"C:\temp\sample.hwp"))
