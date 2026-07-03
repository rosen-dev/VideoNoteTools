import datetime
from utils.os_utils import get_active_process_name
from core.resolve_action import resolve_to_notion
from core.notion_action import notion_to_resolve

def on_hotkey_triggered():
    """
    业务路由中心：
    负责在快捷键触发时，根据当前的活动窗口，将任务分配给不同的业务处理模块。
    """
    try:
        process_name = get_active_process_name()
        
        if "resolve.exe" in process_name:
            resolve_to_notion()
        elif "notion.exe" in process_name:
            notion_to_resolve()
        else:
            print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🚫 防误触机制拦截：忽略操作 (当前程序: {process_name})")
            
    except Exception as e:
        print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [致命错误] 快捷键执行失败: {e}")
