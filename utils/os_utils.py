import time
import datetime
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

def listen_power_events(on_resume_callback):
    """
    监听 Windows 系统电源事件（如休眠唤醒）：
    当检测到系统从 S3/S4/睡眠状态中恢复时，触发 on_resume_callback 回调函数。
    """
    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_POWERBROADCAST:
            if wparam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                log_info("[电源监控] 捕获到 Windows 休眠唤醒信号 (WM_POWERBROADCAST)！")
                try:
                    on_resume_callback()
                except Exception as e:
                    log_error(f"[电源监控] 执行唤醒恢复回调失败: {e}")
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
        log_info("[系统] Windows 休眠/唤醒自动重连监听器已成功开启。")
        win32gui.PumpMessages()
    except Exception as e:
        log_error(f"[电源监控] 注册休眠/唤醒监听器失败: {e}")

def rebind_hotkey(hotkey, notify=False):
    """
    重置并重新绑定全局快捷键（自动修复 Win32 钩子因休眠断开问题）
    """
    from core.router import on_hotkey_triggered

    try:
        keyboard.unhook_all()
    except Exception as e:
        log_info(f"[系统] 清除旧钩子: {e}")
    time.sleep(0.15)
    keyboard.add_hotkey(hotkey, on_hotkey_triggered)
    log_info(f"[系统] 全局快捷键 【{hotkey}】 已重置并成功绑定！")
    if notify:
        show_toast(f"快捷键 【{hotkey}】 已自动恢复激活！", title="休眠唤醒重连", level="info")

def _delayed_rebind(hotkey, notify=False):
    """
    分阶段延时重连机制：
    解决 Windows 刚从休眠唤醒的 0~2 秒内，输入驱动层与消息泵未彻底准备就绪导致钩子挂起的问题。
    """
    log_info("[休眠唤醒] 启动快捷键双阶段恢复序列...")
    time.sleep(0.4)
    rebind_hotkey(hotkey, notify=False)

    time.sleep(1.6)
    rebind_hotkey(hotkey, notify=notify)
    log_info("[休眠唤醒] 快捷键二次加固完毕，现可即时响应。")

def start_background_listener(hotkey):
    """
    后台服务启动器：运行快捷键监听器并启动休眠唤醒监听后台线程
    """
    rebind_hotkey(hotkey)

    def on_power_resume():
        threading.Thread(
            target=_delayed_rebind,
            args=(hotkey, True),
            daemon=True
        ).start()

    threading.Thread(
        target=listen_power_events,
        args=(on_power_resume,),
        daemon=True
    ).start()

    keyboard.wait()
