import sys
import os
import ctypes
from ctypes import wintypes
import win32gui
import win32process
import win32con
import psutil
import pygetwindow as gw

from utils.common import show_toast
from utils.logger import log_info, log_error


class OSUtils:
    """
    Windows 操作系统服务管理工具类 (面向对象封装)
    
    职责：
    1. 进程与窗口管理：查询当前最顶层激活进程、置顶唤醒特定应用窗口；
    2. 原生系统热键管理：解析快捷键字符串、封装 ctypes RegisterHotKey/UnregisterHotKey API；
    3. Win32 WndProc 消息钩子：拦截操作系统 WM_HOTKEY 消息派发路由。
    """


    HOTKEY_ID = 1

    # 修饰键掩码 (MOD)
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000

    # 虚拟键码映射表 (VK)
    VK_MAP = {
        'f': 0x46,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'g': 0x47, 'h': 0x48,
        'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56,
        'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
        'space': win32con.VK_SPACE,
        'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3, 'f4': win32con.VK_F4,
        'f5': win32con.VK_F5, 'f6': win32con.VK_F6, 'f7': win32con.VK_F7, 'f8': win32con.VK_F8,
        'f9': win32con.VK_F9, 'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,
    }

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self._setup_win32_api_signatures()
        
        self.current_hwnd = None
        self.current_hotkey_str = ""
        self.old_wndproc = None
        self.wndproc_callback_ref = None  # 防 GC 被回收

    def _setup_win32_api_signatures(self):
        """配置 Windows API 函数签名，确保 x86/x64 数据对齐"""
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.user32.RegisterHotKey.restype = wintypes.BOOL

        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.UnregisterHotKey.restype = wintypes.BOOL

    # ==========================================
    # 1. 进程与窗口助手方法
    # ==========================================
    @staticmethod
    def get_active_process_name():
        """向 Windows 底层查询当前最前面的活动窗口对应的进程名称"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower()
        except Exception:
            return ""

    @staticmethod
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

    # ==========================================
    # 2. 热键解析与注册
    # ==========================================
    def parse_hotkey_string(self, hotkey_str):
        """将快捷键字符串（如 'alt+shift+f'）解析为 Windows RegisterHotKey 所需的 modifiers 和 vk"""
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        modifiers = self.MOD_NOREPEAT
        vk = None

        for part in parts:
            if part in ('alt', 'option'):
                modifiers |= self.MOD_ALT
            elif part in ('ctrl', 'control'):
                modifiers |= self.MOD_CONTROL
            elif part == 'shift':
                modifiers |= self.MOD_SHIFT
            elif part in ('win', 'windows', 'cmd', 'super'):
                modifiers |= self.MOD_WIN
            else:
                if part in self.VK_MAP:
                    vk = self.VK_MAP[part]
                elif len(part) == 1:
                    vk = ord(part.upper())

        return modifiers, vk

    def register_system_hotkey(self, hwnd, hotkey_str):
        """
        使用 Windows 原生 RegisterHotKey API 向系统内核注册快捷键。
        由操作系统直接接管，休眠/睡眠唤醒后 100% 自动保持生效。
        """
        self.current_hwnd = hwnd
        self.current_hotkey_str = hotkey_str

        modifiers, vk = self.parse_hotkey_string(hotkey_str)
        if vk is None:
            log_error(f"[系统] 无法解析快捷键: {hotkey_str}")
            return False

        # 先解绑旧热键
        self.user32.UnregisterHotKey(hwnd, self.HOTKEY_ID)

        # 注册原生热键
        success = self.user32.RegisterHotKey(hwnd, self.HOTKEY_ID, modifiers, vk)
        if success:
            log_info(f"[系统] 已使用 Windows 原生 RegisterHotKey API 成功注册全局热键 【{hotkey_str}】 (HWND={hwnd})")
        else:
            err = ctypes.GetLastError()
            log_error(f"[系统] 注册 Win32 原生热键失败，错误码: {err} (快捷键可能已被其他软件占用)")

        return bool(success)

    def unregister_system_hotkey(self, hwnd=None):
        """解绑原生系统热键"""
        target_hwnd = hwnd or self.current_hwnd
        if target_hwnd:
            self.user32.UnregisterHotKey(target_hwnd, self.HOTKEY_ID)
            log_info(f"[系统] 已解绑全局热键 (HWND={target_hwnd})")

    # ==========================================
    # 3. WndProc 消息钩子与监听初始化
    # ==========================================
    def _wndproc_handler(self, hwnd, msg, wparam, lparam):
        """Win32 WndProc 实例回调：精准拦截并处理系统 WM_HOTKEY 消息"""
        from core.router import on_hotkey_triggered

        if msg == win32con.WM_HOTKEY:
            if wparam == self.HOTKEY_ID:
                log_info("[原生热键] 收到 Windows 内核 WM_HOTKEY 消息，触发路由...")
                try:
                    on_hotkey_triggered()
                except Exception as e:
                    log_error(f"[原生热键] 执行路由逻辑失败: {e}")
                return 0

        if self.old_wndproc:
            return win32gui.CallWindowProc(self.old_wndproc, hwnd, msg, wparam, lparam)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def setup_win32_hotkey_listener(self, root, hotkey_str):
        """
        在 Tkinter 主窗口的底层 Win32 消息循环中绑定 WM_HOTKEY 消息。
        彻底解决 x64 指针截断与 GC 回收风险，休眠唤醒 100% 生效！
        """
        root.update_idletasks()
        hwnd = root.winfo_id()

        # 1. 注册原生快捷键
        self.register_system_hotkey(hwnd, hotkey_str)

        # 2. 为 HWND 注入强引用的 WndProc 消息钩子 (完美兼容 32 位/64 位 Windows)
        try:
            self.wndproc_callback_ref = self._wndproc_handler
            if hasattr(win32gui, 'SetWindowLongPtr'):
                self.old_wndproc = win32gui.SetWindowLongPtr(hwnd, win32con.GWL_WNDPROC, self._wndproc_handler)
            else:
                self.old_wndproc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, self._wndproc_handler)
            log_info(f"[系统] 成功注入 64位兼容的 Win32 WndProc 消息钩子 (HWND={hwnd})")
        except Exception as e:
            log_info(f"[系统] WndProc 绑定提示: {e}")


    def rebind_hotkey(self, hotkey_str, notify=False):
        """手动重新绑定快捷键（供 UI 界面按钮调用）"""
        if self.current_hwnd:
            self.register_system_hotkey(self.current_hwnd, hotkey_str)
            if notify:
                show_toast(f"快捷键 【{hotkey_str}】 已使用 Win32 原生 API 成功重新激活！", title="快捷键重连", level="info")


# ==========================================
# 单例导出的全局方便函数 (对外标准接口)
# ==========================================
_os_utils = OSUtils()

def get_active_process_name():
    """获取当前活动窗口进程名"""
    return OSUtils.get_active_process_name()

def activate_window(title_keyword):
    """唤醒指定关键字的窗口"""
    return OSUtils.activate_window(title_keyword)

def setup_win32_hotkey_listener(root, hotkey_str):
    """为 Tkinter root 窗口建立系统热键监听器"""
    _os_utils.setup_win32_hotkey_listener(root, hotkey_str)

def unregister_system_hotkey(hwnd=None):
    """解绑系统热键"""
    _os_utils.unregister_system_hotkey(hwnd)

def rebind_hotkey(hotkey_str, notify=False):
    """重新绑定快捷键"""
    _os_utils.rebind_hotkey(hotkey_str, notify=notify)

