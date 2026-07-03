import time
import pyautogui
import pyperclip
import datetime
from utils.common import is_notion_url, show_toast
from utils.os_utils import activate_window
from utils.davinci_utils import find_clip_by_marker_name
from config import DELAY_NOTION_CLIPBOARD

# ==========================================
# 底层动作层 (只负责操作 Notion 软件)
# ==========================================
def extract_url_from_notion():
    """纯底层操作：利用快捷键从 Notion 提取 URL 并返回"""
    print("[动作] 发送快捷键: 'Alt + Shift + L' (Notion原生提取Block链接)")
    pyautogui.hotkey('alt', 'shift', 'l')
    
    print(f"[等待] 等待剪贴板系统写入 ({DELAY_NOTION_CLIPBOARD}秒)...")
    time.sleep(DELAY_NOTION_CLIPBOARD)
    
    url = pyperclip.paste().strip()
    print(f"[状态] 从 Notion 获取到的系统剪贴板内容: '{url}'")
    return url

# ==========================================
# 业务逻辑层 (负责指挥整个跳跃流程)
# ==========================================
def notion_to_resolve():
    """指挥官：调度提取、验证、API搜索与窗口切换"""
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ========================================")
    print("[流程启动] 场景一: Notion -> 达芬奇 (提取链接并跳转)")
    
    # 1. 呼叫底层服务提取 URL
    target_url = extract_url_from_notion()
    
    # 2. 逻辑验证
    if not is_notion_url(target_url):
        print("[错误] 获取到的内容不是合法的 Notion 链接，停止流转。")
        show_toast("抓取失败！\n您当前选中的可能不是一个合法的 Notion Block，或者 Notion 没有响应。")
        return
        
    # 3. 呼叫外部服务 (达芬奇 API)
    print("[动作] 准备调用达芬奇 API 执行全项目搜索...")
    success = find_clip_by_marker_name(target_url)
    
    # 4. 后续处理
    if success:
        print("[动作] API 定位成功，强制唤醒达芬奇窗口。")
        activate_window("DaVinci Resolve")
        pyperclip.copy("")
        print("[动作] 清理残余：已清空系统剪贴板中的 Notion 链接。")
        print("[完成] 跨界跃迁完成！")
    else:
        print("[完成] API 定位失败，流程中止。")
        show_toast("未找到片段！\n\n在达芬奇的当前项目中，没有任何片段的标记标题包含了该 Notion 链接。")
