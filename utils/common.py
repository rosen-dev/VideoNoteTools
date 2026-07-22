import tkinter as tk

def is_notion_url(url):
    """判断字符串中是否包含 Notion 域名"""
    if not url: return False
    return "notion.so" in url or "notion.site" in url or "notion.com" in url

def _create_toast_window(msg, title="提示", level="info", duration=2500):
    """底层绘制非阻塞式的现代悬浮 Toast 窗口"""
    parent = tk._default_root
    temp_root = None
    if parent is None:
        temp_root = tk.Tk()
        temp_root.withdraw()
        parent = temp_root

    try:
        win = tk.Toplevel(parent)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        try:
            win.attributes('-alpha', 0.93)
        except Exception:
            pass

        # 主题色彩方案
        color_map = {
            "info": "#4CAF50",     # 翡翠绿
            "warning": "#FF9800",  # 琥珀黄
            "error": "#F44336"     # 珊瑚红
        }
        accent_color = color_map.get(level, "#4CAF50")
        bg_color = "#2B2B2B"

        # 主卡片容器 (带彩色外边框效果)
        outer_frame = tk.Frame(win, bg=accent_color, padx=2, pady=2)
        outer_frame.pack(fill="both", expand=True)

        inner_frame = tk.Frame(outer_frame, bg=bg_color, padx=18, pady=10)
        inner_frame.pack(fill="both", expand=True)

        if title:
            lbl_title = tk.Label(
                inner_frame,
                text=title,
                font=("Microsoft YaHei UI", 10, "bold"),
                fg=accent_color,
                bg=bg_color,
                anchor="w"
            )
            lbl_title.pack(fill="x", pady=(0, 4))

        lbl_msg = tk.Label(
            inner_frame,
            text=msg,
            font=("Microsoft YaHei UI", 9),
            fg="#F0F0F0",
            bg=bg_color,
            justify="left",
            anchor="w"
        )
        lbl_msg.pack(fill="x")

        # 定位在屏幕顶端居中偏下 (y=60px)
        win.update_idletasks()
        width = win.winfo_reqwidth()
        height = win.winfo_reqheight()
        screen_width = win.winfo_screenwidth()
        x = (screen_width - width) // 2
        y = 60

        win.geometry(f"{width}x{height}+{x}+{y}")

        def destroy_toast():
            try:
                win.destroy()
            except Exception:
                pass
            if temp_root:
                try:
                    temp_root.destroy()
                except Exception:
                    pass

        win.after(duration, destroy_toast)
        if temp_root:
            temp_root.mainloop()
    except Exception as e:
        print(f"[Toast 绘制异常] {e}")

def show_toast(msg, title="提示", level="info", duration=2500):
    """
    非阻塞式悬浮 Toast 提示：
    自动在屏幕上方显示高对比度深色卡片，并在指定毫秒后自行销毁，绝不卡死线程或阻塞快捷键操作。
    """
    if tk._default_root:
        tk._default_root.after(0, lambda: _create_toast_window(msg, title, level, duration))
    else:
        import threading
        threading.Thread(target=lambda: _create_toast_window(msg, title, level, duration), daemon=True).start()

