import tkinter as tk
import json
import os
from utils.os_utils import setup_win32_hotkey_listener, rebind_hotkey, unregister_system_hotkey
from utils.logger import log_info

CONFIG_FILE = "config.json"

# ==========================================
# 核心业务逻辑：配置加载
# ==========================================
def load_config():
    """纯粹的业务函数：负责从磁盘读取配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get("hotkey", "alt+shift+f")
        except:
            pass
    return "alt+shift+f"


# ==========================================
# 界面展示：单纯负责画 UI
# ==========================================
class App:
    def __init__(self, root, hotkey):
        self.root = root
        self.hotkey = hotkey
        self.root.title("DaVinci <-> Notion 跨界桥梁")
        self.root.geometry("450x230")
        self.root.resizable(False, False)
        
        tk.Label(root, text="🚀 后台守望者已就绪", font=("Microsoft YaHei UI", 16, "bold"), fg="#4CAF50").pack(pady=(15, 5))
        tk.Label(root, text=f"当前全局唤醒快捷键: 【{hotkey}】", font=("Microsoft YaHei UI", 11)).pack(pady=3)
        tk.Label(root, text="原生 RegisterHotKey 机制已生效 (支持休眠无感唤醒)", fg="#888888", font=("Microsoft YaHei UI", 9)).pack(pady=(0, 10))

        # 手动重连按钮 (方便用户随时手动重连)
        btn = tk.Button(
            root,
            text="🔄 重新绑定快捷键",
            font=("Microsoft YaHei UI", 10),
            bg="#2B2B2B",
            fg="#FFFFFF",
            activebackground="#3E3E3E",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=4,
            command=self.manual_rebind
        )
        btn.pack(pady=5)

    def manual_rebind(self):
        rebind_hotkey(self.hotkey, notify=True)


if __name__ == "__main__":
    # 1. 独立获取配置
    current_hotkey = load_config()
    
    # 2. 记录启动日志
    log_info("="*60)
    log_info("  DaVinci <-> Notion 双向控制中心 (原生系统热键版) 已启动")
    log_info("="*60)
    log_info(f"[系统] 正在向 Windows 内核注册全局热键: {current_hotkey}")
    log_info("[系统] 仅放行 resolve.exe 和 notion.exe，等待触发中...")
    
    # 3. 初始化 Tkinter 主 UI 窗口
    root = tk.Tk()
    app = App(root, current_hotkey)
    
    # 4. 在底层 Win32 消息循环中注册原生 RegisterHotKey 并监听 WM_HOTKEY 消息
    setup_win32_hotkey_listener(root, current_hotkey)
    
    # 5. 退出时清理系统热键
    root.protocol("WM_DELETE_WINDOW", lambda: (unregister_system_hotkey(), root.destroy()))
    
    # 6. 进入消息泵循环
    root.mainloop()


