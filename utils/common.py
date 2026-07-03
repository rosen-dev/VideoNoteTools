import tkinter as tk
from tkinter import messagebox

def is_notion_url(url):
    """判断字符串中是否包含 Notion 域名"""
    if not url: return False
    return "notion.so" in url or "notion.site" in url or "notion.com" in url

def show_toast(msg):
    """隐形弹窗提示 (UI 显示逻辑)"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showinfo("提示", msg)
    root.destroy()
