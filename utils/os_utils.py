import win32gui
import win32process
import psutil
import pygetwindow as gw
from utils.logger import log_error

def get_active_process_name():
    """向 Windows 底层查询当前最前面的活动窗口对应的进程名称"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().lower()
    except Exception:
        return ""

def activate_window(title_keyword):
    """强制将包含特定关键字的窗口置顶激活"""
    try:
        windows = gw.getWindowsWithTitle(title_keyword)
        for win in windows:
            if win.isMinimized:
                win.restore()
            win.activate()
            return True
    except Exception as e:
        log_error(f"窗口唤醒失败: {e}")
    return False
