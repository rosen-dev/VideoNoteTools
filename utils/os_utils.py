import sys
import os
import time
import subprocess
import threading
import win32gui
import win32process
import win32con
import psutil
import pygetwindow as gw
import keyboard

from utils.common import show_toast
from utils.logger import log_info, log_error

WM_POWERBROADCAST = 0x0218
PBT_APMRESUMEAUTOMATIC = 0x0012
PBT_APMRESUMESUSPEND = 0x0007

_is_restarting = False

def restart_program():
    """
    休眠唤醒终极解决方案：自动重启程序进程。
    重新构建全新的 Win32 消息泵、C 语言钩子线程与硬件上下文，彻底解决 Windows 休眠唤醒导致的钩子挂起失效问题。
    """
    global _is_restarting
    if _is_restarting:
        return
    _is_restarting = True

    log_info("[休眠唤醒] 正在自动重启程序，以彻底重建全新的 Win32 消息循环与全局钩子...")
    time.sleep(0.5)
    try:
        subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd())
    except Exception as e:
        log_error(f"[休眠唤醒] 拉起新进程失败: {e}")
    os._exit(0)

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

def listen_power_events():
    """
    监听 Windows 系统电源事件（如休眠唤醒）：
    当检测到系统从 S3/S4/睡眠状态中恢复时，直接自动重启程序进程。
    """
    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_POWERBROADCAST:
            if wparam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                log_info("[电源监控] 捕获到 Windows 休眠唤醒信号 (WM_POWERBROADCAST)！准备自动重启...")
                threading.Thread(target=restart_program, daemon=True).start()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    try:
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "VideoNoteTools_PowerListener"
        wc.lpfnWndProc = wnd_proc
        class_atom = win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindow(
            class_atom, "PowerListenerWindow", 0, 0, 0, 0, 0, 0, 0, hinst, None
        )
        log_info("[系统] Windows 休眠/唤醒自动重启监听器已成功开启。")
        win32gui.PumpMessages()
    except Exception as e:
        log_error(f"[电源监控] 注册休眠/唤醒监听器失败: {e}")

def rebind_hotkey(hotkey, notify=False):
    """
    重置并重新绑定全局快捷键
    """
    from core.router import on_hotkey_triggered

    try:
        keyboard.unhook_all()
    except Exception as e:
        log_info(f"[系统] 清除旧钩子: {e}")

    try:
        keyboard._listener.listening = False
    except Exception:
        pass

    time.sleep(0.15)
    keyboard.add_hotkey(hotkey, on_hotkey_triggered)
    log_info(f"[系统] 全局快捷键 【{hotkey}】 已重置并成功绑定！")
    if notify:
        show_toast(f"快捷键 【{hotkey}】 已重置激活！", title="快捷键重连", level="info")

def start_background_listener(hotkey):
    """
    后台服务启动器：运行快捷键监听器并启动休眠唤醒监听后台线程
    """
    rebind_hotkey(hotkey)

    # 启动电源事件监听线程
    threading.Thread(
        target=listen_power_events,
        daemon=True
    ).start()

    keyboard.wait()

