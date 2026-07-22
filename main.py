import tkinter as tk
import json
import os
import threading
from utils.os_utils import start_background_listener, rebind_hotkey
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
        tk.Label(root, text="防休眠失灵机制已开启 (休眠唤醒自动重连)", fg="#888888", font=("Microsoft YaHei UI", 9)).pack(pady=(0, 10))

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
    log_info("  DaVinci <-> Notion 双向控制中心 已启动")
    log_info("="*60)
    log_info(f"[系统] 正在监听全局快捷键: {current_hotkey}")
    log_info("[系统] 仅放行 resolve.exe 和 notion.exe，等待触发中...")
    
    # 3. 剥离后台监听逻辑，扔进独立线程
    threading.Thread(target=start_background_listener, args=(current_hotkey,), daemon=True).start()
    
    # 4. 最后画纯粹的 UI 界面
    root = tk.Tk()
    app = App(root, current_hotkey)
    root.mainloop()
