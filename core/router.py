import keyboard
import time
from utils.os_utils import get_active_process_name
from core.resolve_action import resolve_to_notion
from core.notion_action import notion_to_resolve
from config import DELAY_ROUTER_MODIFIER_RELEASE
from utils.logger import log_info, log_error

def on_hotkey_triggered():
    """
    业务路由中心：
    负责在快捷键触发时，根据当前的活动窗口，将任务分配给不同的业务处理模块。
    """
    try:
        # 核心防干扰机制：强行释放物理按键，防止你按住的 Alt 和 Shift 污染后续的盲操按键！
        keyboard.release('alt')
        keyboard.release('shift')
        keyboard.release('ctrl')
        time.sleep(DELAY_ROUTER_MODIFIER_RELEASE)
        
        process_name = get_active_process_name()
        log_info(f"========================================")
        log_info(f"[路由监控] 捕获快捷键触发！当前最顶层激活进程: '{process_name}'")
        
        if "resolve.exe" in process_name:
            resolve_to_notion()
        elif "notion.exe" in process_name:
            notion_to_resolve()
        else:
            log_info(f"[拦截] 防误触机制生效：忽略操作 (当前程序: {process_name})")
            
    except Exception as e:
        log_error(f"[致命错误] 快捷键执行失败: {e}")

