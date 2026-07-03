import time
import pyautogui
import pyperclip
import webbrowser
import datetime
from utils.common import is_notion_url, show_toast
from config import DELAY_PANEL_ANIMATION, DELAY_SHORTCUT_EXEC

# ==========================================
# 底层动作层 (只负责死板地操作达芬奇的面板)
# ==========================================
def extract_title_via_marker_panel():
    """纯底层操作：打出 M 键连招提取当前标记标题"""
    print("[动作] 发送按键: 'M' (调出标记面板)")
    pyautogui.press('m')
    time.sleep(DELAY_PANEL_ANIMATION)
    
    print("[动作] 发送按键: 'Ctrl + C' (复制标题)")
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(DELAY_SHORTCUT_EXEC)
    
    print("[动作] 发送按键: 'Esc' (关闭面板)")
    pyautogui.press('esc')
    time.sleep(DELAY_SHORTCUT_EXEC)
    
    return pyperclip.paste().strip()

def bind_url_via_marker_panel():
    """纯底层操作：打出 M 键连招，将剪贴板内容写入标记标题"""
    print("[动作] 发送按键: 'M' (再次调出面板进行绑定)")
    pyautogui.press('m')
    time.sleep(DELAY_PANEL_ANIMATION)
    
    print("[动作] 发送按键: 'Ctrl + V' (黏贴链接覆盖标题)")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(DELAY_SHORTCUT_EXEC)
    
    print("[动作] 发送按键: 'Enter' (保存并关闭)")
    pyautogui.press('enter')

# ==========================================
# 业务逻辑层 (负责查剪贴板历史、判断是否绑定或跳转)
# ==========================================
def resolve_to_notion():
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ========================================")
    print("[流程启动] 场景二/三: 达芬奇 -> Notion (查询或绑定)")
    
    original_clipboard = pyperclip.paste().strip()
    print(f"[状态] 原始剪贴板内容长度: {len(original_clipboard)} 字符")
    
    pyperclip.copy("")
    print("[动作] 剪贴板已清空，准备执行盲操提取...")
    
    # 1. 呼叫底层服务：尝试提取现有 Marker 标题
    extracted_text = extract_title_via_marker_panel()
    print(f"[状态] 盲操提取到的剪贴板内容: '{extracted_text}'")
    
    # 2. 核心分支判断
    if is_notion_url(extracted_text):
        # 分支 A：跳转
        print("[判断] 提取成功！内容是合法的 Notion 链接，进入跳转流程。")
        notion_app_url = extracted_text.replace("https://", "notion://").replace("http://", "notion://")
        print(f"[动作] 调用系统打开原生协议: {notion_app_url}")
        webbrowser.open(notion_app_url)
        print("[完成] 唤醒 Notion 客户端指令发送完毕。")
        pyperclip.copy(original_clipboard)
    else:
        # 分支 B：绑定或报错
        print("[判断] 提取失败，未检测到 Notion 链接。准备检查是否需要绑定新链接...")
        if is_notion_url(original_clipboard):
            print("[判断] 原始剪贴板中存在 Notion 链接，进入绑定流程！")
            
            pyperclip.copy(original_clipboard)
            time.sleep(0.1)
            
            # 呼叫底层服务：执行绑定写入
            bind_url_via_marker_panel()
            
            print("[完成] 自动打标绑定完毕！")
        else:
            print("[判断] 原始剪贴板中也没有 Notion 链接。流程中止。")
            show_toast("绑定失败：您忘记复制地址了！\n\n请先去 Notion 里复制 Block 链接，然后再回到这里按快捷键进行绑定。")
            pyperclip.copy(original_clipboard)
