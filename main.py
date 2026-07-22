import tkinter as tk
import json
import os
import threading
import keyboard
from core.router import on_hotkey_triggered
from utils.logger import log_info

CONFIG_FILE = "config.json"

# ==========================================
# 核心业务逻辑：路由与配置
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

def start_background_listener(hotkey):
    """纯粹的后台业务：运行死循环监听器"""
    keyboard.add_hotkey(hotkey, on_hotkey_triggered)
    keyboard.wait() 


# ==========================================
# 界面展示：单纯负责画 UI
# ==========================================
class App:
    def __init__(self, root, hotkey):
        self.root = root
        self.root.title("DaVinci <-> Notion 跨界桥梁")
        self.root.geometry("450x200")
        self.root.resizable(False, False)
        
        tk.Label(root, text="🚀 后台守望者已就绪", font=("Arial", 16, "bold"), fg="#4CAF50").pack(pady=15)
        tk.Label(root, text=f"当前全局唤醒快捷键: 【{hotkey}】", font=("Arial", 12)).pack(pady=5)
        tk.Label(root, text="终端调试日志已开启，您可以将此窗口最小化到后台", fg="gray").pack(pady=10)


if __name__ == "__main__":
    # 1. 独立获取配置
    current_hotkey = load_config()
    
    # 2. 记录启动日志
    log_info("="*60)
    log_info("  DaVinci <-> Notion 双向控制中心 已启动")
    log_info("="*60)
    log_info(f"[系统] 正在监听全局快捷键: {current_hotkey}")
    log_info("[系统] 仅放行 resolve.exe 和 notion.exe，等待触发中...\n")
    
    # 3. 剥离后台监听逻辑，扔进独立线程，与 UI 彻底解耦
    threading.Thread(target=start_background_listener, args=(current_hotkey,), daemon=True).start()
    
    # 4. 最后画纯粹的 UI 界面
    root = tk.Tk()
    app = App(root, current_hotkey)
    root.mainloop()
